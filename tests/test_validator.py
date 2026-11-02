import pytest
from src import database, validator


@pytest.fixture(scope="module")
def schema():
    database.init_db()
    return database.get_schema()


def test_valid_select_query(schema):
    """Verify safe SELECT queries are approved."""
    res = validator.validate_sql("SELECT name, salary FROM employees WHERE salary > 50000", schema)
    assert res["valid"] is True
    assert len(res["errors"]) == 0


def test_blocked_keywords(schema):
    """Verify write operations and blocked keywords are rejected."""
    prohibited = [
        "DROP TABLE employees",
        "DELETE FROM employees WHERE id = 1",
        "INSERT INTO departments (name) VALUES ('R&D')",
        "UPDATE employees SET salary = 999999 WHERE id = 1",
        "ALTER TABLE employees ADD COLUMN test TEXT",
        "CREATE TABLE test (id INT)",
        "TRUNCATE employees",
        "PRAGMA foreign_keys = OFF",
    ]
    for sql in prohibited:
        res = validator.validate_sql(sql, schema)
        assert res["valid"] is False, f"Expected blocked keyword failure for: {sql}"
        assert any("Blocked keyword" in err or "Only SELECT" in err for err in res["errors"])


def test_multiple_statements_rejected(schema):
    """Verify semicolon-separated statements are rejected."""
    sql = "SELECT * FROM employees; SELECT * FROM departments;"
    res = validator.validate_sql(sql, schema)
    assert res["valid"] is False
    assert any("single SQL statement" in err for err in res["errors"])


def test_unknown_table_rejected(schema):
    """Verify reference to tables outside allowed set is rejected."""
    sql = "SELECT * FROM secret_passwords"
    res = validator.validate_sql(sql, schema)
    assert res["valid"] is False
    assert any("unknown table" in err.lower() for err in res["errors"])


def test_empty_sql_rejected(schema):
    """Verify empty or whitespace-only SQL is rejected."""
    res = validator.validate_sql("   ", schema)
    assert res["valid"] is False
    assert any("empty" in err.lower() for err in res["errors"])


def test_select_star_warning(schema):
    """Verify SELECT * produces a non-fatal warning."""
    res = validator.validate_sql("SELECT * FROM employees", schema)
    assert res["valid"] is True
    assert len(res["warnings"]) > 0
    assert any("SELECT *" in warn for warn in res["warnings"])

