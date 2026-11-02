# QueryCraft — Test Report

**Student:** Tanay Siddharth Shelar  
**Student ID:** 150096725092  
**Test Suite Status:** 43 PASSED / 0 FAILED (100% Pass Rate)  
**Execution Runtime:** 0.79 seconds  

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
collected 43 items

tests/test_ai_generator.py::test_load_prompt_all_versions PASSED         [  2%]
tests/test_ai_generator.py::test_load_prompt_invalid_version PASSED      [  4%]
tests/test_ai_generator.py::test_extract_sql_varieties PASSED            [  6%]
tests/test_ai_generator.py::test_model_configuration_loading PASSED      [  9%]
tests/test_ai_generator.py::test_api_key_loading PASSED                  [ 11%]
tests/test_ai_generator.py::test_gemini_api_key_missing_error PASSED     [ 13%]
tests/test_ai_generator.py::test_model_discovery_excludes_obsolete_models PASSED [ 16%]
tests/test_ai_generator.py::test_model_not_found_classification_and_sanitization PASSED [ 18%]
tests/test_ai_generator.py::test_quota_error_classification PASSED       [ 20%]
tests/test_ai_generator.py::test_network_error_classification PASSED     [ 23%]
tests/test_ai_generator.py::test_invalid_key_classification PASSED       [ 25%]
tests/test_ai_generator.py::test_gemini_generation_mocked PASSED         [ 27%]
tests/test_ai_generator.py::test_invalid_model_response_rejected PASSED  [ 30%]
tests/test_ai_generator.py::test_api_key_missing_error PASSED            [ 32%]
tests/test_ai_generator.py::test_openai_api_error_handling_sanitized PASSED [ 34%]
tests/test_automation.py::test_automation_empty_question PASSED          [ 37%]
tests/test_automation.py::test_automation_workflow_end_to_end_mocked_ai PASSED [ 39%]
tests/test_automation.py::test_automation_ai_generation_failure_model_not_found PASSED [ 41%]
tests/test_automation.py::test_automation_preserves_ai_error_when_storage_fails PASSED [ 44%]
tests/test_automation.py::test_automation_cannot_answer_handling PASSED  [ 46%]
tests/test_automation.py::test_run_all_reference_tests_automation PASSED [ 48%]
tests/test_database.py::test_db_init_creates_tables_and_data PASSED      [ 51%]
tests/test_database.py::test_get_schema_and_schema_text PASSED           [ 53%]
tests/test_database.py::test_execute_query_valid_select PASSED           [ 55%]
tests/test_database.py::test_execute_query_readonly_pragma PASSED        [ 58%]
tests/test_database.py::test_execute_query_empty_error PASSED            [ 60%]
tests/test_database.py::test_execute_query_database_failure PASSED       [ 62%]
tests/test_evaluator.py::test_reference_cases_definitions PASSED         [ 65%]
tests/test_evaluator.py::test_reference_cases_execution PASSED           [ 67%]
tests/test_evaluator.py::test_semantic_correctness_vs_execution_success PASSED [ 69%]
tests/test_evaluator.py::test_evaluate_edge_case_expected_error PASSED   [ 72%]
tests/test_storage.py::test_storage_init PASSED                          [ 74%]
tests/test_storage.py::test_save_and_retrieve_run PASSED                 [ 76%]
tests/test_storage.py::test_save_reference_test_run PASSED               [ 79%]
tests/test_storage.py::test_fresh_database_initialization_and_schema_creation PASSED [ 81%]
tests/test_storage.py::test_saving_failed_workflow_run PASSED            [ 83%]
tests/test_storage.py::test_legacy_schema_migration_without_data_loss PASSED [ 86%]
tests/test_validator.py::test_valid_select_query PASSED                  [ 88%]
tests/test_validator.py::test_blocked_keywords PASSED                    [ 90%]
tests/test_validator.py::test_multiple_statements_rejected PASSED        [ 93%]
tests/test_validator.py::test_unknown_table_rejected PASSED              [ 95%]
tests/test_validator.py::test_empty_sql_rejected PASSED                  [ 97%]
tests/test_validator.py::test_select_star_warning PASSED                 [100%]

============================== 43 passed in 0.79s ==============================
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
| **AI Integration & Error Handling** | `test_load_prompt_all_versions` | Confirms `v1`, `v2`, `v3` template loading and placeholder integrity | ✅ PASS |
| | `test_load_prompt_invalid_version` | Confirms unknown prompt version raises `ValueError` | ✅ PASS |
| | `test_extract_sql_varieties` | Tests markdown fences (````sql ... ````, ```` ... ````, raw) parsing | ✅ PASS |
| | `test_model_configuration_loading` | Confirms Gemini model configuration loads from secrets/env | ✅ PASS |
| | `test_api_key_loading` | Confirms `GEMINI_API_KEY` loads from secrets/env | ✅ PASS |
| | `test_gemini_api_key_missing_error` | Confirms missing Gemini key triggers categorized `MISSING_API_KEY` | ✅ PASS |
| | `test_model_discovery_excludes_obsolete_models` | Confirms dynamic model discovery filters out `gemini-1.5-pro` and embeddings | ✅ PASS |
| | `test_model_not_found_classification_and_sanitization` | Confirms HTTP 404 is categorized as `MODEL_NOT_FOUND` and redacts keys | ✅ PASS |
| | `test_quota_error_classification` | Confirms HTTP 429 is categorized as `QUOTA_EXHAUSTED` | ✅ PASS |
| | `test_network_error_classification` | Confirms timeouts/socket errors are categorized as `NETWORK_ERROR` | ✅ PASS |
| | `test_invalid_key_classification` | Confirms HTTP 400/401/403 invalid key errors are categorized as `INVALID_API_KEY` | ✅ PASS |
| | `test_gemini_generation_mocked` | Confirms valid Gemini generateContent extraction | ✅ PASS |
| | `test_invalid_model_response_rejected` | Confirms empty/filtered LLM responses raise `INVALID_RESPONSE` | ✅ PASS |
| | `test_api_key_missing_error` | Confirms missing OpenAI API key raises `EnvironmentError` | ✅ PASS |
| | `test_openai_api_error_handling_sanitized` | Confirms OpenAI API error sanitization | ✅ PASS |
| **Automation & Storage Resilience** | `test_automation_empty_question` | Confirms pipeline aborts safely when input is empty | ✅ PASS |
| | `test_automation_workflow_end_to_end_mocked_ai` | Confirms full trigger-action pipeline: Input → AI → Validation → Execution → Storage | ✅ PASS |
| | `test_automation_ai_generation_failure_model_not_found` | Confirms AI generation failure skips SQL execution and records failure | ✅ PASS |
| | `test_automation_preserves_ai_error_when_storage_fails` | Confirms storage failure does NOT hide or crash primary AI exception | ✅ PASS |
| | `test_automation_cannot_answer_handling` | Confirms AI `CANNOT_ANSWER` response stops execution and logs audit trail | ✅ PASS |
| | `test_storage_init` | Confirms storage tables initialize idempotently | ✅ PASS |
| | `test_save_and_retrieve_run` | Confirms runs persist in SQLite `runs` table with unique Run IDs | ✅ PASS |
| | `test_save_reference_test_run` | Confirms reference benchmark run logging | ✅ PASS |
| | `test_fresh_database_initialization_and_schema_creation` | Confirms fresh DB path initializes all 13 columns cleanly | ✅ PASS |
| | `test_saving_failed_workflow_run` | Confirms failed runs preserve `error_message` and `error_category` | ✅ PASS |
| | `test_legacy_schema_migration_without_data_loss` | Confirms older 11-column tables migrate dynamically without losing data | ✅ PASS |
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
- **Online Mode:** Google Gemini API integration (`google-genai` official SDK) with dynamic model discovery, support for `gemini-2.0-flash`, `gemini-2.5-flash`, and `gemini-3.8-flash`, plus optional OpenAI fallback. All secrets are managed securely via Streamlit Secrets and `.env` with complete redaction from logs and error banners.
