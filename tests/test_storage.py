import uuid
import pytest
from src import database, storage


@pytest.fixture(autouse=True)
def setup_db():
    database.init_db()
    storage.init_storage()


def test_storage_init():
    """Verify storage initializes tables."""
    storage.init_storage()
    # Should be idempotent


def test_save_and_retrieve_run():
    """Verify saving a run and retrieving it from history."""
    run_id = f"RUN-TEST-{uuid.uuid4().hex[:6]}"
    sample_data = {
        "columns": ["id", "name", "salary"],
        "rows": [{"id": 1, "name": "Alice Nguyen", "salary": 115000.0}],
        "row_count": 1,
    }

    saved_id = storage.save_run(
        run_id=run_id,
        question="Show Alice Nguyen",
        prompt_version="v2_structured",
        validation_status="valid",
        execution_status="success",
        generated_sql="SELECT id, name, salary FROM employees WHERE name = 'Alice Nguyen'",
        row_count=1,
        result_data=sample_data,
        error_message=None,
    )
    assert saved_id == run_id

    history = storage.get_history(limit=10)
    assert len(history) >= 1
    recent = next(r for r in history if r["run_id"] == run_id)
    assert recent["question"] == "Show Alice Nguyen"
    assert recent["prompt_version"] == "v2_structured"
    assert recent["validation_status"] == "valid"
    assert recent["execution_status"] == "success"
    assert recent["row_count"] == 1
    assert "Alice Nguyen" in recent["result_json"]


def test_save_reference_test_run():
    """Verify reference test result can be saved."""
    test_result = {
        "test_id": "TC001",
        "passed": True,
        "reason": "Row count matched",
        "details": {"rows": 20},
    }
    # Should not raise any error
    storage.save_reference_test_result(test_result)
