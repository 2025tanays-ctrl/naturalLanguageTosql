import re
import uuid
from datetime import datetime
from typing import Optional

from src import ai_generator, database, evaluator, storage, validator


def generate_run_id() -> str:
    """Generate a clean, readable unique run ID."""
    return f"RUN-{uuid.uuid4().hex[:8].upper()}"


def find_matching_reference_case(question: str) -> Optional[dict]:
    """Find a reference test case matching the question (ignoring punctuation & case)."""
    clean_q = re.sub(r"[^\w\s]", "", question.strip().lower())
    for tc in evaluator.REFERENCE_CASES:
        clean_tc_q = re.sub(r"[^\w\s]", "", tc["question"].lower())
        if clean_q == clean_tc_q:
            return tc
    return None


def run_workflow(
    question: str,
    prompt_version: str = "v2_structured",
    model: str = "gemini-2.0-flash",
) -> dict:
    """
    Execute the full end-to-end trigger-action workflow:
      1. Validate user input
      2. Retrieve schema & prompt template to call AI generator
      3. Validate generated SQL for safety and schema correctness
      4. Execute approved read-only query on SQLite
      5. Evaluate against reference answers (if applicable)
      6. Persist run in SQLite storage
      7. Return results dict with unique run ID
    """
    run_id = generate_run_id()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    stages = {
        "input": {"valid": True, "question": question.strip()},
        "generation": {
            "success": False,
            "sql": "",
            "raw_response": "",
            "model": model,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "error": None,
        },
        "validation": {
            "valid": False,
            "errors": [],
            "warnings": [],
        },
        "execution": {
            "success": False,
            "data": None,
            "error": None,
        },
        "evaluation": None,
    }

    # 1. Input Validation
    q_stripped = question.strip()
    if not q_stripped or len(q_stripped) < 3:
        err = "Question is too short or empty. Please enter a meaningful question."
        stages["input"]["valid"] = False
        stages["generation"]["error"] = err
        stages["execution"]["error"] = "Execution skipped due to empty or invalid question."
        storage.save_run(
            run_id=run_id,
            question=question,
            prompt_version=prompt_version,
            validation_status="invalid_input",
            execution_status="skipped",
            generated_sql=None,
            row_count=0,
            result_data=None,
            error_message=err,
            timestamp=now_str,
        )
        return {"run_id": run_id, "stages": stages}

    # 2. Schema retrieval & AI generation
    try:
        schema = database.get_schema()
        schema_text = database.get_schema_text()
        prompt_template = ai_generator.load_prompt(prompt_version)
    except Exception as exc:
        err = f"Setup failed: {exc}"
        stages["generation"]["error"] = err
        stages["execution"]["error"] = "Execution skipped due to setup error."
        storage.save_run(
            run_id=run_id,
            question=question,
            prompt_version=prompt_version,
            validation_status="setup_error",
            execution_status="skipped",
            generated_sql=None,
            row_count=0,
            result_data=None,
            error_message=err,
            timestamp=now_str,
        )
        return {"run_id": run_id, "stages": stages}

    try:
        gen_res = ai_generator.generate_sql(
            question=q_stripped,
            prompt_template=prompt_template,
            schema_text=schema_text,
            model=model,
        )
        stages["generation"].update(
            {
                "success": True,
                "sql": gen_res["sql"],
                "raw_response": gen_res.get("raw_response", ""),
                "model": gen_res.get("model", model),
                "prompt_tokens": gen_res.get("prompt_tokens", 0),
                "completion_tokens": gen_res.get("completion_tokens", 0),
            }
        )
        generated_sql = gen_res["sql"]
    except Exception as exc:
        err = str(exc)
        stages["generation"]["error"] = err
        stages["execution"]["error"] = "Execution skipped due to AI generation error."
        storage.save_run(
            run_id=run_id,
            question=question,
            prompt_version=prompt_version,
            validation_status="generation_failed",
            execution_status="skipped",
            generated_sql=None,
            row_count=0,
            result_data=None,
            error_message=err,
            timestamp=now_str,
        )
        return {"run_id": run_id, "stages": stages}

    # Handle CANNOT_ANSWER signal from AI
    if generated_sql.startswith("CANNOT_ANSWER:"):
        reason = generated_sql[len("CANNOT_ANSWER:") :].strip()
        stages["validation"] = {
            "valid": False,
            "errors": [f"Question cannot be answered using the schema: {reason}"],
            "warnings": [],
        }
        stages["execution"]["error"] = "Execution skipped because AI determined schema cannot satisfy question."

        matched_tc = find_matching_reference_case(question)
        if matched_tc:
            stages["evaluation"] = evaluator.evaluate_result(
                matched_tc, None, f"CANNOT_ANSWER: {reason}"
            )

        storage.save_run(
            run_id=run_id,
            question=question,
            prompt_version=prompt_version,
            validation_status="cannot_answer",
            execution_status="skipped",
            generated_sql=generated_sql,
            row_count=0,
            result_data=None,
            error_message=reason,
            timestamp=now_str,
        )
        return {"run_id": run_id, "stages": stages}

    # 3. SQL Validation
    val_res = validator.validate_sql(generated_sql, schema)
    stages["validation"] = val_res

    validation_status = "valid" if val_res["valid"] else "invalid"

    # 4. SQL Execution
    exec_data = None
    exec_error = None
    execution_status = "skipped"

    if val_res["valid"]:
        try:
            exec_data = database.execute_query(generated_sql)
            stages["execution"] = {
                "success": True,
                "data": exec_data,
                "error": None,
            }
            execution_status = "success"
        except Exception as exc:
            exec_error = str(exc)
            stages["execution"] = {
                "success": False,
                "data": None,
                "error": exec_error,
            }
            execution_status = "failed"
    else:
        exec_error = "Validation rejected the SQL: " + "; ".join(val_res["errors"])
        stages["execution"]["error"] = exec_error

    # 5. Verification against reference cases (if applicable)
    matched_tc = find_matching_reference_case(question)
    if matched_tc:
        stages["evaluation"] = evaluator.evaluate_result(
            matched_tc,
            exec_data,
            exec_error if not val_res["valid"] or execution_status != "success" else None,
        )

    # 6. Storage persistence
    row_count = exec_data.get("row_count") if exec_data else 0
    storage.save_run(
        run_id=run_id,
        question=question,
        prompt_version=prompt_version,
        validation_status=validation_status,
        execution_status=execution_status,
        generated_sql=generated_sql,
        row_count=row_count,
        result_data=exec_data,
        error_message=exec_error,
        timestamp=now_str,
    )

    return {"run_id": run_id, "stages": stages}


def run_all_reference_tests() -> list[dict]:
    """
    Run all 5 reference test cases directly against the database,
    evaluate results, save them to storage, and return formatted results.
    """
    results: list[dict] = []
    for test_case in evaluator.REFERENCE_CASES:
        expected_sql: Optional[str] = test_case.get("expected_sql")
        actual_result: Optional[dict] = None
        error: Optional[str] = None

        if expected_sql is None:
            error = f"No SQL query available for '{test_case['id']}' (expected error test)."
        else:
            try:
                actual_result = database.execute_query(expected_sql)
            except Exception as exc:
                error = str(exc)

        eval_out = evaluator.evaluate_result(test_case, actual_result, error)

        # Enhance details with rows and columns for table display
        details = dict(eval_out.get("details", {}))
        if actual_result:
            details["rows"] = actual_result.get("rows", [])
            details["columns"] = actual_result.get("columns", [])
        elif error:
            details["error"] = error

        res = {
            "test_id": test_case["id"],
            "question": test_case["question"],
            "passed": eval_out["passed"],
            "reason": eval_out["reason"],
            "sql": expected_sql,
            "details": details,
        }

        # Save to database
        try:
            storage.save_reference_test_result(res)
        except Exception:
            pass

        results.append(res)

    return results
