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


def test_fresh_database_initialization_and_schema_creation(tmp_path, monkeypatch):
    """Verify fresh database initialization creates all tables and columns from scratch."""
    test_db = tmp_path / "fresh_test.db"
    monkeypatch.setenv("QUERYCRAFT_DB_PATH", str(test_db))

    assert not test_db.exists()
    storage.init_storage()
    assert test_db.exists()

    conn = storage.get_storage_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(runs)")
        cols = {row[1] for row in cursor.fetchall()}
        expected_cols = {
            "id", "run_id", "timestamp", "question", "prompt_version",
            "generated_sql", "validation_status", "execution_status",
            "row_count", "result_json", "error_message", "model", "error_category"
        }
        assert expected_cols.issubset(cols)
    finally:
        conn.close()


def test_saving_failed_workflow_run():
    """Verify saving a failed workflow run preserves error message and category."""
    run_id = f"RUN-FAIL-{uuid.uuid4().hex[:6]}"
    saved_id = storage.save_run(
        run_id=run_id,
        question="Show bad query",
        prompt_version="v2_structured",
        validation_status="generation_failed",
        execution_status="skipped",
        generated_sql=None,
        row_count=0,
        result_data=None,
        error_message="Model gemini-1.5-pro not found",
        model="gemini-1.5-pro",
        error_category="MODEL_NOT_FOUND",
    )
    assert saved_id == run_id

    history = storage.get_history(limit=5)
    run_entry = next(r for r in history if r["run_id"] == run_id)
    assert run_entry["validation_status"] == "generation_failed"
    assert run_entry["execution_status"] == "skipped"
    assert run_entry["model"] == "gemini-1.5-pro"
    assert run_entry["error_category"] == "MODEL_NOT_FOUND"
    assert "Model gemini-1.5-pro not found" in run_entry["error_message"]


def test_legacy_schema_migration_without_data_loss(tmp_path, monkeypatch):
    """Verify an older runs table (missing model & error_category) is migrated cleanly on save."""
    import sqlite3
    test_db = tmp_path / "legacy.db"
    monkeypatch.setenv("QUERYCRAFT_DB_PATH", str(test_db))

    # Create older schema from commit 1ead193 (no model, no error_category)
    conn = sqlite3.connect(str(test_db))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE runs (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id            TEXT UNIQUE NOT NULL,
            timestamp         TEXT NOT NULL,
            question          TEXT NOT NULL,
            prompt_version    TEXT NOT NULL,
            generated_sql     TEXT,
            validation_status TEXT NOT NULL,
            execution_status  TEXT NOT NULL,
            row_count         INTEGER,
            result_json       TEXT,
            error_message     TEXT
        );
    """)
    # Seed old record
    c.execute("""
        INSERT INTO runs (run_id, timestamp, question, prompt_version, validation_status, execution_status)
        VALUES ('RUN-OLD-01', '2026-01-01 10:00:00', 'Old question', 'v1', 'valid', 'success');
    """)
    conn.commit()
    conn.close()

    # Calling save_run on legacy DB should automatically migrate and succeed
    new_run_id = f"RUN-MIGRATE-{uuid.uuid4().hex[:6]}"
    saved_id = storage.save_run(
        run_id=new_run_id,
        question="New question after migration",
        prompt_version="v3_refined",
        validation_status="valid",
        execution_status="success",
        generated_sql="SELECT 1",
        row_count=1,
        model="gemini-3.8-flash",
        error_category=None,
    )
    assert saved_id == new_run_id

    # Verify both old and new records are readable
    history = storage.get_history(limit=10)
    assert any(r["run_id"] == "RUN-OLD-01" for r in history)
    new_entry = next(r for r in history if r["run_id"] == new_run_id)
    assert new_entry["model"] == "gemini-3.8-flash"
