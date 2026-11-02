from unittest.mock import patch
import pytest
from src import automation, database, storage, ai_generator


@pytest.fixture(autouse=True)
def setup_env():
    database.init_db()
    storage.init_storage()


def test_automation_empty_question():
    """Verify empty question fails early without calling AI."""
    res = automation.run_workflow(question="   ", prompt_version="v2_structured")
    assert res["run_id"].startswith("RUN-")
    assert res["stages"]["input"]["valid"] is False
    assert res["stages"]["execution"]["success"] is False


def test_automation_workflow_end_to_end_mocked_ai():
    """Verify the full trigger-action pipeline with mocked AI response."""
    mock_sql = "SELECT id, name, salary FROM employees WHERE salary > 100000"
    mock_ai_output = {
        "sql": mock_sql,
        "raw_response": f"```sql\n{mock_sql}\n```",
        "model": "gemini-3.8-flash",
        "prompt_tokens": 120,
        "completion_tokens": 25,
    }

    with patch("src.ai_generator.generate_sql", return_value=mock_ai_output):
        res = automation.run_workflow(
            question="Show employees earning over 100000",
            prompt_version="v2_structured",
            model="gemini-3.8-flash",
        )

        assert res["run_id"].startswith("RUN-")
        assert res["stages"]["input"]["valid"] is True
        assert res["stages"]["generation"]["success"] is True
        assert res["stages"]["validation"]["valid"] is True
        assert res["stages"]["execution"]["success"] is True
        assert res["stages"]["execution"]["data"]["row_count"] >= 1

        # Check that it was saved in storage with model and error category
        history = storage.get_history(limit=5)
        matched = [r for r in history if r["run_id"] == res["run_id"]]
        assert len(matched) == 1
        assert matched[0]["validation_status"] == "valid"
        assert matched[0]["execution_status"] == "success"
        assert matched[0]["model"] == "gemini-3.8-flash"


def test_automation_ai_generation_failure_model_not_found():
    """Verify that when AI generation fails with MODEL_NOT_FOUND, SQL execution is skipped and audit logs record the error."""
    err = ai_generator.AIProviderError(
        "Model 'gemini-1.5-pro' is not found for API version v1beta",
        category="MODEL_NOT_FOUND",
        model="gemini-1.5-pro",
    )
    with patch("src.ai_generator.generate_sql", side_effect=err):
        res = automation.run_workflow(
            question="Show all employees",
            model="gemini-1.5-pro",
        )
        assert res["stages"]["generation"]["success"] is False
        assert res["stages"]["generation"]["error_category"] == "MODEL_NOT_FOUND"
        assert res["stages"]["execution"]["success"] is False
        assert "MODEL_NOT_FOUND" in res["stages"]["execution"]["error"]

        # Check storage
        history = storage.get_history(limit=5)
        matched = next(r for r in history if r["run_id"] == res["run_id"])
        assert matched["validation_status"] == "generation_failed"
        assert matched["execution_status"] == "skipped"
        assert matched["model"] == "gemini-1.5-pro"
        assert matched["error_category"] == "MODEL_NOT_FOUND"


def test_automation_preserves_ai_error_when_storage_fails():
    """Verify that if storage raises an OperationalError, the primary AI exception is preserved."""
    import sqlite3

    ai_err = ai_generator.AIProviderError(
        message="Model gemini-3.8-flash is not found (HTTP 404)",
        category="MODEL_NOT_FOUND",
        model="gemini-3.8-flash",
    )

    with patch("src.ai_generator.generate_sql", side_effect=ai_err):
        with patch("src.storage.save_run", side_effect=sqlite3.OperationalError("table runs locked")):
            res = automation.run_workflow(
                question="Show all employees",
                model="gemini-3.8-flash",
            )

            # Workflow did not crash
            assert res is not None
            assert res["run_id"].startswith("RUN-")

            # Original AI error preserved
            assert res["stages"]["generation"]["success"] is False
            assert "Model gemini-3.8-flash is not found (HTTP 404)" in res["stages"]["generation"]["error"]
            assert res["stages"]["generation"]["error_category"] == "MODEL_NOT_FOUND"

            # Execution was skipped
            assert res["stages"]["execution"]["success"] is False

            # Storage failure recorded separately without hiding AI error
            assert res["stages"]["storage"]["saved"] is False
            assert "table runs locked" in res["stages"]["storage"]["error"]


def test_automation_cannot_answer_handling():
    """Verify workflow gracefully handles CANNOT_ANSWER from AI."""
    mock_ai_output = {
        "sql": "CANNOT_ANSWER: The schema does not contain employee phone numbers.",
        "raw_response": "CANNOT_ANSWER: The schema does not contain employee phone numbers.",
        "model": "gemini-3.8-flash",
        "prompt_tokens": 100,
        "completion_tokens": 15,
    }

    with patch("src.ai_generator.generate_sql", return_value=mock_ai_output):
        res = automation.run_workflow(
            question="Show employee phone numbers",
            prompt_version="v3_refined",
            model="gemini-3.8-flash",
        )

        assert res["run_id"].startswith("RUN-")
        assert res["stages"]["validation"]["valid"] is False
        assert res["stages"]["execution"]["success"] is False
        assert "cannot be answered" in res["stages"]["validation"]["errors"][0].lower()
        # Matched TC005 evaluation should pass because error was expected!
        assert res["stages"]["evaluation"] is not None
        assert res["stages"]["evaluation"]["passed"] is True


def test_run_all_reference_tests_automation():
    """Verify run_all_reference_tests runs 5 cases and returns properly formatted dicts."""
    results = automation.run_all_reference_tests()
    assert len(results) == 5
    for r in results:
        assert "test_id" in r
        assert "question" in r
        assert "passed" in r
        assert "reason" in r
        assert "details" in r
        assert r["passed"] is True
