import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src.database import get_db_path


def init_storage() -> None:
    """Create the runs and reference_test_runs tables if they do not exist."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
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
                error_message     TEXT,
                model             TEXT,
                error_category    TEXT
            );
        """)

        # Backward compatibility: ensure model and error_category columns exist
        cursor.execute("PRAGMA table_info(runs)")
        existing_cols = {col[1] for col in cursor.fetchall()}
        if "model" not in existing_cols:
            cursor.execute("ALTER TABLE runs ADD COLUMN model TEXT")
        if "error_category" not in existing_cols:
            cursor.execute("ALTER TABLE runs ADD COLUMN error_category TEXT")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reference_test_runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id     TEXT NOT NULL,
                run_at      TEXT NOT NULL,
                passed      INTEGER NOT NULL,
                reason      TEXT,
                details_json TEXT
            );
        """)
        conn.commit()
    finally:
        conn.close()


def save_run(
    run_id: str,
    question: str,
    prompt_version: str,
    validation_status: str,
    execution_status: str,
    generated_sql: Optional[str] = None,
    row_count: Optional[int] = None,
    result_data: Optional[dict] = None,
    error_message: Optional[str] = None,
    timestamp: Optional[str] = None,
    model: Optional[str] = None,
    error_category: Optional[str] = None,
) -> str:
    """
    Persist a query generation & execution run to SQLite.
    
    Returns:
        The run_id string.
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    result_json = None
    if result_data is not None:
        try:
            result_json = json.dumps(result_data, default=str)
        except Exception:
            result_json = str(result_data)

    conn = sqlite3.connect(str(get_db_path()))
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO runs (
                run_id, timestamp, question, prompt_version,
                generated_sql, validation_status, execution_status,
                row_count, result_json, error_message, model, error_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                timestamp,
                question,
                prompt_version,
                generated_sql,
                validation_status,
                execution_status,
                row_count,
                result_json,
                error_message,
                model,
                error_category,
            ),
        )
        conn.commit()
        return run_id
    finally:
        conn.close()


def get_history(limit: int = 50) -> list[dict]:
    """Retrieve the most recent query runs from storage."""
    conn = sqlite3.connect(str(get_db_path()))
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT run_id, timestamp, question, prompt_version,
                   generated_sql, validation_status, execution_status,
                   row_count, result_json, error_message, model, error_category
            FROM runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def save_reference_test_result(test_result: dict) -> None:
    """Save an individual reference test execution result."""
    conn = sqlite3.connect(str(get_db_path()))
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO reference_test_runs (test_id, run_at, passed, reason, details_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                test_result.get("test_id", "UNKNOWN"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                1 if test_result.get("passed") else 0,
                test_result.get("reason", ""),
                json.dumps(test_result.get("details", {}), default=str),
            ),
        )
        conn.commit()
    finally:
        conn.close()
