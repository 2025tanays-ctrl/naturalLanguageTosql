import pytest
from src import database, evaluator


@pytest.fixture(autouse=True)
def setup_db():
    database.init_db()


def test_reference_cases_definitions():
    """Verify all 5 reference test cases exist with expected properties."""
    assert len(evaluator.REFERENCE_CASES) == 5
    ids = [tc["id"] for tc in evaluator.REFERENCE_CASES]
    assert ids == ["TC001", "TC002", "TC003", "TC004", "TC005"]


def test_reference_cases_execution():
    """Verify all 5 reference cases evaluate successfully with expected outputs."""
    results = evaluator.run_reference_tests(database.execute_query)
    assert len(results) == 5
    for r in results:
        assert r["passed"] is True, f"Reference test {r['test_id']} failed: {r['reason']}"


def test_semantic_correctness_vs_execution_success():
    """
    Verify that execution success is cleanly distinguished from semantic correctness.
    A query like 'SELECT name FROM employees LIMIT 3' executes without database error,
    but fails the TC004 requirement of returning the 5 highest paid employees.
    """
    tc004 = next(tc for tc in evaluator.REFERENCE_CASES if tc["id"] == "TC004")

    # This query succeeds syntactically and in SQLite execution:
    flawed_result = database.execute_query("SELECT name FROM employees LIMIT 3")
    assert flawed_result["row_count"] == 3

    # But semantic evaluation must fail because expected rows = 5
    eval_outcome = evaluator.evaluate_result(tc004, flawed_result, None)
    assert eval_outcome["passed"] is False
    assert "Exact row count mismatch: expected 5, got 3" in eval_outcome["reason"]


def test_evaluate_edge_case_expected_error():
    """Verify TC005 correctly evaluates error handling when an unsupported column is queried."""
    tc005 = next(tc for tc in evaluator.REFERENCE_CASES if tc["id"] == "TC005")

    # Simulated error when attempting to query nonexistent column 'phone'
    eval_outcome = evaluator.evaluate_result(
        tc005, None, "OperationalError: no such column: phone"
    )
    assert eval_outcome["passed"] is True
    assert "Expected an error and got one" in eval_outcome["reason"]

