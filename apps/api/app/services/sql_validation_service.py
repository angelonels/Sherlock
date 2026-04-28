from __future__ import annotations

import re
from dataclasses import dataclass

import sqlglot
from sqlglot import exp


BLOCKED_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "grant",
    "revoke",
    "copy",
    "execute",
    "call",
}
BLOCKED_SCHEMAS = {"public", "information_schema", "pg_catalog"}
UNSAFE_FUNCTIONS = {"pg_sleep", "dblink", "lo_import", "lo_export"}


@dataclass(frozen=True)
class SqlValidationResult:
    is_valid: bool
    sql: str | None = None
    error: str | None = None


class SqlValidationService:
    def validate(self, sql: str, *, table_name: str, allowed_columns: set[str]) -> SqlValidationResult:
        lowered = sql.lower()
        if "--" in sql or "/*" in sql or "*/" in sql:
            return SqlValidationResult(False, error="Comments are not allowed.")
        if ";" in sql.strip().rstrip(";"):
            return SqlValidationResult(False, error="Multiple statements are not allowed.")
        if re.search(r"\b(" + "|".join(BLOCKED_KEYWORDS) + r")\b", lowered):
            return SqlValidationResult(False, error="Only read-only SELECT statements are allowed.")

        try:
            expressions = sqlglot.parse(sql, read="postgres")
        except Exception as exc:
            return SqlValidationResult(False, error=f"SQL parse failed: {exc}")
        if len(expressions) != 1:
            return SqlValidationResult(False, error="Exactly one SQL statement is allowed.")
        expression = expressions[0]
        if not isinstance(expression, (exp.Select, exp.With)):
            return SqlValidationResult(False, error="Only SELECT and WITH queries are allowed.")

        cte_names = {cte.alias for cte in expression.find_all(exp.CTE) if cte.alias}
        for table in expression.find_all(exp.Table):
            schema = table.db
            name = table.name
            if not schema and name in cte_names:
                continue
            if schema in BLOCKED_SCHEMAS:
                return SqlValidationResult(False, error=f"Schema {schema} is not allowed.")
            if schema != "user_data" or name != table_name:
                return SqlValidationResult(False, error="Query can only read the current dataset table.")

        for func in expression.find_all(exp.Func):
            if func.sql_name().lower() in UNSAFE_FUNCTIONS:
                return SqlValidationResult(False, error="Unsafe SQL function is not allowed.")

        for column in expression.find_all(exp.Column):
            column_name = column.name
            if column_name.startswith("_sherlock_"):
                continue
            if column_name not in allowed_columns:
                return SqlValidationResult(False, error=f"Unknown or unauthorized column: {column_name}")

        validated_sql = sql.strip().rstrip(";")
        if not expression.args.get("limit"):
            validated_sql = f"{validated_sql} LIMIT 1000"
        return SqlValidationResult(True, sql=validated_sql)
