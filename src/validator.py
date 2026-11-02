import re
import sqlglot
from sqlglot import exp

ALLOWED_TABLES: set[str] = {"employees", "departments"}

BLOCKED_KEYWORDS: set[str] = {
    "insert", "update", "delete", "drop", "alter", "create",
    "truncate", "replace", "attach", "detach", "pragma", "vacuum", "reindex",
}


def validate_sql(sql: str, schema: dict) -> dict:
    """
    Validate a SQL string for safety and structural correctness.

    Args:
        sql:    Raw SQL string to validate.
        schema: Schema dict returned by database.get_schema().

    Returns:
        {
            "valid":    bool,
            "errors":   list[str],   # fatal issues
            "warnings": list[str],   # non-fatal concerns
        }
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Not empty
    sql = sql.strip()
    if not sql:
        return {"valid": False, "errors": ["SQL query is empty."], "warnings": []}

    # 2. Blocked keyword check (word-boundary, case-insensitive)
    lower_sql = sql.lower()
    for kw in BLOCKED_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", lower_sql):
            errors.append(f"Blocked keyword detected: '{kw}'.")

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings}

    # 3. Parse with sqlglot
    try:
        statements = sqlglot.parse(sql, dialect="sqlite")
    except sqlglot.errors.ParseError as exc:
        errors.append(f"SQL parse error: {exc}")
        return {"valid": False, "errors": errors, "warnings": warnings}

    if not statements or len(statements) == 0:
        errors.append("No SQL statement found.")
        return {"valid": False, "errors": errors, "warnings": warnings}

    if len(statements) > 1:
        errors.append(f"Only a single SQL statement is allowed; got {len(statements)}.")
        return {"valid": False, "errors": errors, "warnings": warnings}

    stmt = statements[0]

    # 4. Must be a SELECT
    if not isinstance(stmt, exp.Select):
        stmt_type = type(stmt).__name__
        errors.append(f"Only SELECT statements are allowed; got '{stmt_type}'.")
        return {"valid": False, "errors": errors, "warnings": warnings}

    # 5. Extract all referenced table names from AST
    referenced_tables: set[str] = set()
    for table_node in stmt.find_all(exp.Table):
        tbl_name = table_node.name.lower() if table_node.name else ""
        if tbl_name:
            referenced_tables.add(tbl_name)

    unknown_tables = referenced_tables - ALLOWED_TABLES
    if unknown_tables:
        errors.append(
            f"Query references unknown table(s): {', '.join(sorted(unknown_tables))}. "
            f"Allowed tables: {', '.join(sorted(ALLOWED_TABLES))}."
        )

    # 6. Check for subquery writes (e.g. INSERT INTO ... SELECT)
    for subquery in stmt.find_all(exp.Subquery):
        inner = subquery.this
        if isinstance(inner, (exp.Insert, exp.Update, exp.Delete)):
            errors.append("Subquery contains a write operation, which is not permitted.")

    # 7. Warn about SELECT * on large-ish tables
    for select_star in stmt.find_all(exp.Star):
        warnings.append(
            "Using SELECT * is discouraged; consider selecting only the columns you need."
        )
        break  # warn once

    valid = len(errors) == 0
    return {"valid": valid, "errors": errors, "warnings": warnings}
