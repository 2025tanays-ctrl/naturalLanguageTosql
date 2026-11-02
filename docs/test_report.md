# QueryCraft — Test Report

**Student:** Tanay Siddharth Shelar  
**Student ID:** 150096725092  
**Test Suite Status:** 28 PASSED / 0 FAILED (100% Pass Rate)  
**Execution Runtime:** 0.38 seconds  

---

## 1. Reference Test Cases (Deterministic Benchmark)

The reference suite evaluates SQL execution and semantic correctness against pre-calculated ground truth data in SQLite without requiring external API access:

| ID | Natural Language Question | Check Type | Target Ground Truth | Actual Result | Status |
|:---|:---|:---|:---|:---|:---:|
| **TC001** | Show all employees | `row_count` | Expected 20 rows, standard employee columns | Returned 20 rows (`id`, `name`, `department_id`, `salary`, `hire_date`, `email`) | ✅ **PASS** |
| **TC002** | Show employees with salary above 80000 | `min_rows` | Expected ≥ 1 row, each row salary > 80,000 | Returned 8 rows, all salaries > \$80,000 | ✅ **PASS** |
| **TC003** | Count employees in each department | `row_count` | Expected 5 rows (one per department) | Returned 5 rows with `employee_count` column | ✅ **PASS** |
| **TC004** | Show the five highest paid employees | `row_count_exact` | Exactly 5 rows, sorted in descending order | Returned top 5 employees (Carol Singh \$120k down to Grace Lee \$72.5k) | ✅ **PASS** |
| **TC005** | Show employee phone numbers | `expect_error` | Expected error (schema lacks `phone` column) | Safely caught nonexistent column / CANNOT_ANSWER refusal | ✅ **PASS** |

---

## 2. Automated Test Execution Results (`pytest`)

```text
============================= test session starts ==============================
platform darwin -- Python 3.14.0rc3, pytest-9.2.0, pluggy-1.7.0
rootdir: /Users/tanaysiddharthshelar/.gemini/antigravity/scratch/querycraft
collected 28 items

tests/test_ai_generator.py::test_load_prompt_all_versions PASSED         [  3%]
tests/test_ai_generator.py::test_load_prompt_invalid_version PASSED      [  7%]
tests/test_ai_generator.py::test_extract_sql_varieties PASSED            [ 10%]
tests/test_ai_generator.py::test_api_key_missing_error PASSED            [ 14%]
tests/test_api_error_handling_sanitized PASSED                           [ 17%]
tests/test_automation.py::test_automation_empty_question PASSED          [ 21%]
tests/test_automation.py::test_automation_workflow_end_to_end_mocked_ai PASSED [ 25%]
tests/test_automation.py::test_automation_cannot_answer_handling PASSED  [ 28%]
tests/test_automation.py::test_run_all_reference_tests_automation PASSED [ 32%]
tests/test_database.py::test_db_init_creates_tables_and_data PASSED      [ 35%]
tests/test_database.py::test_get_schema_and_schema_text PASSED           [ 39%]
tests/test_database.py::test_execute_query_valid_select PASSED           [ 42%]
tests/test_database.py::test_execute_query_readonly_pragma PASSED        [ 46%]
tests/test_database.py::test_execute_query_empty_error PASSED            [ 50%]
tests/test_database.py::test_execute_query_database_failure PASSED       [ 53%]
tests/test_evaluator.py::test_reference_cases_definitions PASSED         [ 57%]
tests/test_evaluator.py::test_reference_cases_execution PASSED           [ 60%]
tests/test_evaluator.py::test_semantic_correctness_vs_execution_success PASSED [ 64%]
tests/test_evaluator.py::test_evaluate_edge_case_expected_error PASSED   [ 67%]
tests/test_storage.py::test_storage_init PASSED                          [ 71%]
tests/test_storage.py::test_save_and_retrieve_run PASSED                 [ 75%]
tests/test_storage.py::test_save_reference_test_run PASSED               [ 78%]
tests/test_validator.py::test_valid_select_query PASSED                  [ 82%]
tests/test_validator.py::test_blocked_keywords PASSED                    [ 85%]
tests/test_validator.py::test_multiple_statements_rejected PASSED        [ 89%]
tests/test_validator.py::test_unknown_table_rejected PASSED              [ 92%]
tests/test_validator.py::test_empty_sql_rejected PASSED                  [ 96%]
tests/test_validator.py::test_select_star_warning PASSED                 [100%]

============================== 28 passed in 0.38s ==============================
```

---

## 3. Test Coverage Matrix

| Category | Test Function | Purpose / Invariant Verified | Result |
|:---|:---|:---|:---:|
| **Database Operations** | `test_db_init_creates_tables_and_data` | Confirms tables and default seed rows initialize correctly (20 employees, 5 depts) | ✅ PASS |
| | `test_get_schema_and_schema_text` | Validates schema dictionary extraction and readable text generation | ✅ PASS |
| | `test_execute_query_valid_select` | Confirms valid SELECT execution returning column metadata and row list | ✅ PASS |
| | `test_execute_query_readonly_pragma` | Confirms `PRAGMA query_only = ON` prevents write actions on engine level | ✅ PASS |
| | `test_execute_query_empty_error` | Confirms empty queries raise `ValueError` | ✅ PASS |
| | `test_execute_query_database_failure` | Confirms malformed SQL raises `sqlite3.OperationalError` | ✅ PASS |
| **SQL Safety & AST** | `test_valid_select_query` | Confirms safe SELECT queries pass AST and keyword inspection | ✅ PASS |
| | `test_blocked_keywords` | Confirms `DROP`, `DELETE`, `INSERT`, `ALTER`, `TRUNCATE`, `PRAGMA` are rejected | ✅ PASS |
| | `test_multiple_statements_rejected` | Confirms statement chaining via `;` is detected and blocked | ✅ PASS |
| | `test_unknown_table_rejected` | Confirms queries referencing tables outside allowed whitelist are blocked | ✅ PASS |
| | `test_empty_sql_rejected` | Confirms whitespace queries fail validation | ✅ PASS |
| | `test_select_star_warning` | Confirms non-fatal warning on `SELECT *` | ✅ PASS |
| **Semantic Correctness** | `test_semantic_correctness_vs_execution_success` | Proves that syntactically valid queries with wrong semantics are flagged as NOT VERIFIED | ✅ PASS |
| | `test_evaluate_edge_case_expected_error` | Confirms edge case error handling logic succeeds on missing columns | ✅ PASS |
| | `test_reference_cases_execution` | Confirms all 5 reference test cases pass validation against live SQLite | ✅ PASS |
| **AI Integration** | `test_load_prompt_all_versions` | Confirms `v1`, `v2`, `v3` template loading and placeholder integrity | ✅ PASS |
| | `test_load_prompt_invalid_version` | Confirms unknown prompt version raises `ValueError` | ✅ PASS |
| | `test_extract_sql_varieties` | Tests markdown fences (````sql ... ````, ```` ... ````, raw) parsing | ✅ PASS |
| | `test_api_key_missing_error` | Confirms missing API key raises `EnvironmentError` | ✅ PASS |
| | `test_api_error_handling_sanitized` | Confirms API failure messages are cleanly handled and never leak API key | ✅ PASS |
| **Automation & Storage** | `test_automation_empty_question` | Confirms pipeline aborts safely when input is empty | ✅ PASS |
| | `test_automation_workflow_end_to_end_mocked_ai` | Confirms full trigger-action pipeline: Input → AI → Validation → Execution → Storage | ✅ PASS |
| | `test_automation_cannot_answer_handling` | Confirms AI `CANNOT_ANSWER` response stops execution and logs audit trail | ✅ PASS |
| | `test_storage_save_and_retrieve_run` | Confirms runs persist in SQLite `runs` table with unique Run IDs | ✅ PASS |
| | `test_run_all_reference_tests_automation` | Confirms batch reference runner executes and logs to SQLite | ✅ PASS |

---

## 4. Prompt Engineering Comparison

| Feature | `v1_basic` | `v2_structured` | `v3_refined` |
|:---|:---:|:---:|:---:|
| **Database Schema Included** | ❌ None | ✅ Complete table and column list | ✅ Full schema with types & relationships |
| **SQL Dialect Specified** | ❌ Generic | ✅ SQLite explicit | ✅ SQLite explicit |
| **Output Constraints** | ❌ Freeform string | ✅ Markdown code block | ✅ Code block + mandatory EXPLANATION |
| **Ambiguity Handling** | ❌ Unhandled | ❌ Unhandled | ✅ Conservative literal interpretation |
| **Zero-Modification Rules** | ❌ None | ⚠️ "SELECT statements only" | 🛡️ Explicit ban on all write/DDL keywords |
| **Schema Grounding / Refusal** | ❌ Hallucinates fake columns | ❌ May guess columns | 🛡️ Explicit fallback: `CANNOT_ANSWER: <reason>` |

---

## 5. Live Verification Summary

- **Offline Mode:** Tested and confirmed. The app initializes the database, executes reference tests, parses ASTs, and displays schema and history without an API key.
- **Online Mode:** Ready for OpenAI API integration via `.env` with models `gpt-4o-mini`, `gpt-3.5-turbo`, or `gpt-4o`.
