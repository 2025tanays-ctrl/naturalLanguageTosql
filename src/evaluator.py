import json
from typing import Any, Callable

REFERENCE_CASES: list[dict] = [
    {
        "id": "TC001",
        "question": "Show all employees",
        "expected_sql": "SELECT * FROM employees",
        "expected_row_count": 20,
        "expected_columns": ["id", "name", "department_id", "salary", "hire_date", "email"],
        "check_type": "row_count",
    },
    {
        "id": "TC002",
        "question": "Show employees with salary above 80000",
        "expected_sql": "SELECT * FROM employees WHERE salary > 80000",
        "min_row_count": 1,
        "check_type": "min_rows",
        "salary_check": {"column": "salary", "min": 80000},
    },
    {
        "id": "TC003",
        "question": "Count employees in each department",
        "expected_sql": (
            "SELECT d.name, COUNT(e.id) as employee_count "
            "FROM departments d "
            "LEFT JOIN employees e ON d.id = e.department_id "
            "GROUP BY d.id, d.name"
        ),
        "expected_row_count": 5,
        "expected_columns_include": ["employee_count"],
        "check_type": "row_count",
    },
    {
        "id": "TC004",
        "question": "Show the five highest paid employees",
        "expected_sql": (
            "SELECT name, salary FROM employees ORDER BY salary DESC LIMIT 5"
        ),
        "expected_row_count": 5,
        "check_type": "row_count_exact",
    },
    {
        "id": "TC005",
        "question": "Show employee phone numbers",
        "expected_sql": None,
        "expected_error": "phone",
        "check_type": "expect_error",
    },
]


def evaluate_result(
    test_case: dict,
    actual_result: dict | None,
    error: str | None,
) -> dict:
    """
    Evaluate the outcome of a single test case.

    Args:
        test_case:     One entry from REFERENCE_CASES.
        actual_result: Dict returned by execute_query, or None if execution failed.
        error:         Error message string if any step failed, else None.

    Returns:
        {
            "test_id": str,
            "passed":  bool,
            "reason":  str,
            "details": dict,
        }
    """
    test_id: str = test_case.get("id", "UNKNOWN")
    check_type: str = test_case.get("check_type", "")
    details: dict[str, Any] = {
        "question":    test_case.get("question"),
        "check_type":  check_type,
        "error":       error,
        "actual_result_summary": (
            {
                "row_count": actual_result.get("row_count"),
                "columns":   actual_result.get("columns"),
            }
            if actual_result
            else None
        ),
    }

    # ------------------------------------------------------------------ #
    # check_type: expect_error                                             #
    # ------------------------------------------------------------------ #
    if check_type == "expect_error":
        if error is not None:
            return {
                "test_id": test_id,
                "passed":  True,
                "reason":  f"Expected an error and got one: {error}",
                "details": details,
            }
        # No error — check whether the result columns mention the banned concept
        expected_error_hint: str = test_case.get("expected_error", "")
        if actual_result is not None:
            columns_str = " ".join(actual_result.get("columns", [])).lower()
            if expected_error_hint and expected_error_hint.lower() not in columns_str:
                return {
                    "test_id": test_id,
                    "passed":  True,
                    "reason":  (
                        f"Expected error about '{expected_error_hint}' — "
                        "column not present, so query was appropriately rejected."
                    ),
                    "details": details,
                }
        return {
            "test_id": test_id,
            "passed":  False,
            "reason":  "Expected an error but query succeeded unexpectedly.",
            "details": details,
        }

    # ------------------------------------------------------------------ #
    # All other checks require a successful result                        #
    # ------------------------------------------------------------------ #
    if actual_result is None:
        return {
            "test_id": test_id,
            "passed":  False,
            "reason":  f"Execution failed with error: {error}",
            "details": details,
        }

    actual_row_count: int = actual_result.get("row_count", 0)
    actual_columns: list[str] = actual_result.get("columns", [])

    # ------------------------------------------------------------------ #
    # check_type: row_count                                                #
    # ------------------------------------------------------------------ #
    if check_type == "row_count":
        expected_row_count: int = test_case.get("expected_row_count", 0)

        # Optional column presence check
        expected_cols_include: list[str] = test_case.get("expected_columns_include", [])
        missing_cols = [
            c for c in expected_cols_include if c not in actual_columns
        ]
        if missing_cols:
            return {
                "test_id": test_id,
                "passed":  False,
                "reason":  f"Missing expected columns: {missing_cols}.",
                "details": details,
            }

        # Optional exact column check
        expected_columns: list[str] | None = test_case.get("expected_columns")
        if expected_columns and sorted(actual_columns) != sorted(expected_columns):
            return {
                "test_id": test_id,
                "passed":  False,
                "reason":  (
                    f"Column mismatch. Expected {expected_columns}, "
                    f"got {actual_columns}."
                ),
                "details": details,
            }

        passed = actual_row_count == expected_row_count
        return {
            "test_id": test_id,
            "passed":  passed,
            "reason":  (
                f"Row count {'matches' if passed else 'mismatch'}: "
                f"expected {expected_row_count}, got {actual_row_count}."
            ),
            "details": details,
        }

    # ------------------------------------------------------------------ #
    # check_type: row_count_exact                                          #
    # ------------------------------------------------------------------ #
    if check_type == "row_count_exact":
        expected_row_count = test_case.get("expected_row_count", 0)
        passed = actual_row_count == expected_row_count
        return {
            "test_id": test_id,
            "passed":  passed,
            "reason":  (
                f"Exact row count {'matches' if passed else 'mismatch'}: "
                f"expected {expected_row_count}, got {actual_row_count}."
            ),
            "details": details,
        }

    # ------------------------------------------------------------------ #
    # check_type: min_rows                                                 #
    # ------------------------------------------------------------------ #
    if check_type == "min_rows":
        min_row_count: int = test_case.get("min_row_count", 1)

        # Optional salary / numeric range check
        salary_check: dict | None = test_case.get("salary_check")
        if salary_check and actual_result.get("rows"):
            col = salary_check.get("column", "salary")
            minimum = salary_check.get("min")
            if minimum is not None:
                violators = [
                    row for row in actual_result["rows"]
                    if col in row and row[col] is not None and row[col] <= minimum
                ]
                if violators:
                    return {
                        "test_id": test_id,
                        "passed":  False,
                        "reason":  (
                            f"{len(violators)} row(s) violate the salary filter "
                            f"({col} > {minimum})."
                        ),
                        "details": details,
                    }

        passed = actual_row_count >= min_row_count
        return {
            "test_id": test_id,
            "passed":  passed,
            "reason":  (
                f"Min row count {'met' if passed else 'not met'}: "
                f"expected >= {min_row_count}, got {actual_row_count}."
            ),
            "details": details,
        }

    # ------------------------------------------------------------------ #
    # Unknown check_type                                                   #
    # ------------------------------------------------------------------ #
    return {
        "test_id": test_id,
        "passed":  False,
        "reason":  f"Unknown check_type '{check_type}'.",
        "details": details,
    }


def run_reference_tests(execute_fn: Callable[[str], dict]) -> list[dict]:
    """
    Run all REFERENCE_CASES using the provided execute_fn.

    Args:
        execute_fn: Callable that accepts a SQL string and returns a result dict
                    (or raises on error).

    Returns:
        List of evaluation result dicts (one per test case).
    """
    results: list[dict] = []

    for test_case in REFERENCE_CASES:
        expected_sql: str | None = test_case.get("expected_sql")
        actual_result: dict | None = None
        error: str | None = None

        if expected_sql is None:
            # Nothing to execute — expect an error state
            error = f"No SQL defined for test case '{test_case['id']}' (expected_error scenario)."
        else:
            try:
                actual_result = execute_fn(expected_sql)
            except Exception as exc:
                error = str(exc)

        result = evaluate_result(test_case, actual_result, error)
        results.append(result)

    return results
