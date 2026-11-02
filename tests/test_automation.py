from unittest.mock import patch
import pytest
from src import automation, database, storage


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
        "model": "gpt-4o-mini",
        "prompt_tokens": 120,
        "completion_tokens": 25,
    }

    with patch("src.ai_generator.generate_sql", return_value=mock_ai_output):
        res = automation.run_workflow(
            question="Show employees earning over 100000",
            prompt_version="v2_structured",
        )

        assert res["run_id"].startswith("RUN-")
        assert res["stages"]["input"]["valid"] is True
        assert res["stages"]["generation"]["success"] is True
        assert res["stages"]["validation"]["valid"] is True
        assert res["stages"]["execution"]["success"] is True
        assert res["stages"]["execution"]["data"]["row_count"] >= 1

        # Check that it was saved in storage
        history = storage.get_history(limit=5)
        matched = [r for r in history if r["run_id"] == res["run_id"]]
        assert len(matched) == 1
        assert matched[0]["validation_status"] == "valid"
        assert matched[0]["execution_status"] == "success"


def test_automation_cannot_answer_handling():
    """Verify workflow gracefully handles CANNOT_ANSWER from AI."""
    mock_ai_output = {
        "sql": "CANNOT_ANSWER: The schema does not contain employee phone numbers.",
        "raw_response": "CANNOT_ANSWER: The schema does not contain employee phone numbers.",
        "model": "gpt-4o-mini",
        "prompt_tokens": 100,
        "completion_tokens": 15,
    }

    with patch("src.ai_generator.generate_sql", return_value=mock_ai_output):
        res = automation.run_workflow(
            question="Show employee phone numbers",
            prompt_version="v3_refined",
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

