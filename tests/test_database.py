import sqlite3
import pytest
from src import database


def test_db_init_creates_tables_and_data():
    """Verify database initializes properly with correct seed row counts."""
    database.init_db()
    conn = sqlite3.connect(str(database.get_db_path()))
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM departments")
        dept_count = cursor.fetchone()[0]
        assert dept_count == 5, f"Expected 5 departments, found {dept_count}"

        cursor.execute("SELECT COUNT(*) FROM employees")
        emp_count = cursor.fetchone()[0]
        assert emp_count == 20, f"Expected 20 employees, found {emp_count}"
    finally:
        conn.close()


def test_get_schema_and_schema_text():
    """Verify get_schema returns expected dictionary structure and tables."""
    schema = database.get_schema()
    assert "employees" in schema
    assert "departments" in schema

    emp_cols = [c["name"] for c in schema["employees"]]
    assert "id" in emp_cols
    assert "name" in emp_cols
    assert "salary" in emp_cols
    assert "department_id" in emp_cols

    schema_text = database.get_schema_text()
    assert "Database Schema" in schema_text
    assert "employees" in schema_text
    assert "departments" in schema_text


def test_execute_query_valid_select():
    """Verify a valid SELECT query executes and returns correct structure."""
    result = database.execute_query("SELECT id, name, salary FROM employees ORDER BY salary DESC LIMIT 5")
    assert "columns" in result
    assert "rows" in result
    assert "row_count" in result
    assert result["row_count"] == 5
    assert result["columns"] == ["id", "name", "salary"]
    assert len(result["rows"]) == 5
    # First row should be the highest earner (Carol Singh, 120,000)
    assert result["rows"][0]["name"] == "Carol Singh"
    assert result["rows"][0]["salary"] == 120000.0


def test_execute_query_readonly_pragma():
    """Verify that execute_query operates with query-only mode enabled."""
    with pytest.raises(sqlite3.Error):
        database.execute_query("INSERT INTO departments (id, name) VALUES (99, 'Hacking')")


def test_execute_query_empty_error():
    """Verify executing empty SQL raises ValueError."""
    with pytest.raises(ValueError, match="SQL query must not be empty"):
        database.execute_query("   ")


def test_execute_query_database_failure():
    """Verify executing malformed SQL raises sqlite3.OperationalError."""
    with pytest.raises(sqlite3.OperationalError):
        database.execute_query("SELECT nonexistent_column FROM nonexistent_table")

