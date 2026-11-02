import os
import sqlite3
import json
from pathlib import Path
from typing import Optional


def get_db_path() -> Path:
    """
    Return the path to the main QueryCraft SQLite database.
    Checks QUERYCRAFT_DB_PATH in env/secrets before falling back to default.
    """
    env_path = os.environ.get("QUERYCRAFT_DB_PATH")
    if env_path:
        return Path(env_path)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "QUERYCRAFT_DB_PATH" in st.secrets:
            return Path(str(st.secrets["QUERYCRAFT_DB_PATH"]))
    except Exception:
        pass
    return Path(__file__).parent.parent / "data" / "querycraft.db"


def init_db() -> None:
    """Create tables and populate with realistic fictional data."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()

        # --- Schema ---
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS departments (
                id       INTEGER PRIMARY KEY,
                name     TEXT    NOT NULL,
                location TEXT,
                budget   REAL
            );

            CREATE TABLE IF NOT EXISTS employees (
                id            INTEGER PRIMARY KEY,
                name          TEXT    NOT NULL,
                department_id INTEGER REFERENCES departments(id),
                salary        REAL,
                hire_date     TEXT,
                email         TEXT
            );
        """)

        # --- Departments ---
        departments = [
            (1, "Engineering",   "San Francisco, CA", 4_500_000.00),
            (2, "Marketing",     "New York, NY",      2_000_000.00),
            (3, "Sales",         "Chicago, IL",       3_000_000.00),
            (4, "Human Resources","Austin, TX",        1_200_000.00),
            (5, "Finance",       "Boston, MA",        1_800_000.00),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO departments (id, name, location, budget) VALUES (?,?,?,?)",
            departments,
        )

        # --- Employees ---
        employees = [
            # Engineering (dept 1)
            (1,  "Alice Nguyen",      1, 115_000.00, "2019-03-15", "alice.nguyen@querycraft.io"),
            (2,  "Bob Martinez",      1,  98_500.00, "2020-07-22", "bob.martinez@querycraft.io"),
            (3,  "Carol Singh",       1, 120_000.00, "2018-01-10", "carol.singh@querycraft.io"),
            (4,  "David Kim",         1,  87_000.00, "2021-11-03", "david.kim@querycraft.io"),
            (5,  "Evelyn Clarke",     1,  75_000.00, "2022-05-17", "evelyn.clarke@querycraft.io"),
            # Marketing (dept 2)
            (6,  "Frank O'Brien",     2,  68_000.00, "2020-09-01", "frank.obrien@querycraft.io"),
            (7,  "Grace Lee",         2,  72_500.00, "2019-12-20", "grace.lee@querycraft.io"),
            (8,  "Henry Patel",       2,  55_000.00, "2023-02-28", "henry.patel@querycraft.io"),
            (9,  "Isla Rodriguez",    2,  81_000.00, "2017-06-05", "isla.rodriguez@querycraft.io"),
            # Sales (dept 3)
            (10, "Jack Thompson",     3,  62_000.00, "2021-04-14", "jack.thompson@querycraft.io"),
            (11, "Karen Wilson",      3,  95_000.00, "2016-08-30", "karen.wilson@querycraft.io"),
            (12, "Liam Brown",        3,  48_000.00, "2022-10-11", "liam.brown@querycraft.io"),
            (13, "Mia Johnson",       3,  57_500.00, "2020-01-25", "mia.johnson@querycraft.io"),
            (14, "Noah Davis",        3,  73_000.00, "2018-11-07", "noah.davis@querycraft.io"),
            # Human Resources (dept 4)
            (15, "Olivia Garcia",     4,  52_000.00, "2021-07-19", "olivia.garcia@querycraft.io"),
            (16, "Peter White",       4,  61_000.00, "2019-05-23", "peter.white@querycraft.io"),
            (17, "Quinn Harris",      4,  45_500.00, "2023-03-06", "quinn.harris@querycraft.io"),
            # Finance (dept 5)
            (18, "Rachel Adams",      5,  88_000.00, "2017-02-14", "rachel.adams@querycraft.io"),
            (19, "Samuel Turner",     5, 105_000.00, "2015-09-09", "samuel.turner@querycraft.io"),
            (20, "Tina Moore",        5,  30_000.00, "2024-01-02", "tina.moore@querycraft.io"),
        ]
        cursor.executemany(
            """INSERT OR IGNORE INTO employees
               (id, name, department_id, salary, hire_date, email)
               VALUES (?,?,?,?,?,?)""",
            employees,
        )

        conn.commit()
    finally:
        conn.close()


def get_schema() -> dict:
    """Return schema as {table_name: [{"name", "type", "pk", "notnull"}, ...]}."""
    conn = sqlite3.connect(str(get_db_path()))
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        schema = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            rows = cursor.fetchall()
            # PRAGMA table_info columns: cid, name, type, notnull, dflt_value, pk
            schema[table] = [
                {
                    "name":    row[1],
                    "type":    row[2],
                    "pk":      bool(row[5]),
                    "notnull": bool(row[3]),
                }
                for row in rows
            ]
        return schema
    finally:
        conn.close()


def get_schema_text() -> str:
    """Return a human-readable text description of the database schema."""
    schema = get_schema()
    lines = ["Database Schema", "=" * 40]
    for table, columns in schema.items():
        lines.append(f"\nTable: {table}")
        lines.append("-" * 30)
        for col in columns:
            flags = []
            if col["pk"]:
                flags.append("PRIMARY KEY")
            if col["notnull"]:
                flags.append("NOT NULL")
            flag_str = f"  [{', '.join(flags)}]" if flags else ""
            lines.append(f"  {col['name']} {col['type']}{flag_str}")
    return "\n".join(lines)


def get_readonly_connection():
    """Return a read-only sqlite3 connection via URI mode."""
    db_path = get_db_path().resolve()
    uri = f"file:{db_path}?mode=ro"
    return sqlite3.connect(uri, uri=True, check_same_thread=False)


def execute_query(sql: str, max_rows: int = 100, timeout: float = 5.0) -> dict:
    """
    Execute a SQL query safely and return results as a dict.

    Returns:
        {"columns": [...], "rows": [...], "row_count": N}

    Raises:
        ValueError: if the query is empty or produces no parseable result.
        sqlite3.Error: on database / SQL errors.
        RuntimeError: on timeout or other runtime issues.
    """
    sql = sql.strip()
    if not sql:
        raise ValueError("SQL query must not be empty.")

    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path), detect_types=sqlite3.PARSE_DECLTYPES, timeout=timeout)
    try:
        conn.execute("PRAGMA query_only = ON")

        def dict_factory(cursor, row):
            return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

        conn.row_factory = dict_factory
        cursor = conn.cursor()
        cursor.execute(sql)

        rows = cursor.fetchmany(max_rows)
        columns = [col[0] for col in cursor.description] if cursor.description else []

        return {
            "columns":   columns,
            "rows":      rows,
            "row_count": len(rows),
        }
    except sqlite3.OperationalError as exc:
        raise sqlite3.OperationalError(f"Query execution failed: {exc}") from exc
    except sqlite3.Error as exc:
        raise sqlite3.Error(f"Database error: {exc}") from exc
    finally:
        conn.close()
