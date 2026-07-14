from __future__ import annotations

import re

import sqlglot
from sqlglot import exp


ALLOWED_TABLES = {
    "users",
    "products",
    "orders",
    "order_items",
    "user_events",
}

SYSTEM_SCHEMAS = {"pg_catalog", "information_schema"}

FORBIDDEN_EXPRESSION_TYPES = tuple(
    node_type
    for node_type in (
        getattr(exp, "Insert", None),
        getattr(exp, "Update", None),
        getattr(exp, "Delete", None),
        getattr(exp, "Drop", None),
        getattr(exp, "Alter", None),
        getattr(exp, "Truncate", None),
        getattr(exp, "Create", None),
        getattr(exp, "Grant", None),
        getattr(exp, "Revoke", None),
        getattr(exp, "Merge", None),
        getattr(exp, "Command", None),
    )
    if node_type is not None
)


def _normalize_sql_text(text: str) -> str:
    """Normalize trailing semicolons while keeping one consistent suffix."""
    stripped = text.strip().rstrip(";").strip()
    return f"{stripped};" if stripped else stripped


def _strip_code_fences(text: str) -> str:
    """Extract the content of the first fenced code block when present."""
    code_block_match = re.search(
        r"```(?:sql)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL
    )
    if code_block_match:
        return code_block_match.group(1).strip()
    return text.strip()


def _candidate_sql_texts(text: str) -> list[str]:
    """Build likely SQL candidates from raw LLM output."""
    fenced = _strip_code_fences(text)
    candidates = [fenced]

    # If the model added a short explanation, try the first SELECT/WITH span too.
    pattern = re.compile(r"(?is)\b(select|with)\b")
    starts = [match.start() for match in pattern.finditer(fenced)]
    for start in starts:
        candidate = fenced[start:].strip()
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    return candidates


def _parse_sql_candidate(sql: str) -> exp.Expression:
    """Parse a single PostgreSQL statement and surface a clean error on failure."""
    statements = sqlglot.parse(sql, read="postgres")
    if len(statements) != 1:
        raise ValueError("Multiple SQL statements are not allowed")

    try:
        return sqlglot.parse_one(sql, dialect="postgres")
    except sqlglot.errors.ParseError as exc:
        raise ValueError("Invalid SQL") from exc


def _collect_cte_names(expression: exp.Expression) -> set[str]:
    """Collect local CTE names so we do not mistake them for real tables."""
    cte_names: set[str] = set()
    for cte in expression.find_all(exp.CTE):
        alias = getattr(cte, "alias_or_name", None)
        if alias:
            cte_names.add(str(alias).lower())
    return cte_names


def _extract_table_name(table: exp.Table) -> str:
    """Return the visible table name from a sqlglot table node."""
    return str(getattr(table, "name", "")).lower()


def _extract_schema_name(table: exp.Table) -> str:
    """Return the schema/database part from a sqlglot table node."""
    db = getattr(table, "db", None)
    return str(db).lower() if db else ""


def _has_forbidden_expression(expression: exp.Expression) -> bool:
    """Detect disallowed statement types anywhere in the parsed tree."""
    for node_type in FORBIDDEN_EXPRESSION_TYPES:
        if node_type and expression.find(node_type):
            return True
    return False


def extract_sql_from_llm_output(output: str) -> str:
    """Extract SQL from raw LLM output and normalize trailing semicolons."""
    text = output.strip()

    for candidate in _candidate_sql_texts(text):
        normalized = candidate.strip()
        if not normalized:
            continue

        # Prefer the first parseable SELECT/WITH chunk when the model adds prose.
        try:
            parsed = sqlglot.parse_one(normalized, dialect="postgres")
        except sqlglot.errors.ParseError:
            continue

        if isinstance(parsed, exp.Select):
            return _normalize_sql_text(normalized)

    return _normalize_sql_text(text)


def validate_select_sql(sql: str) -> None:
    """Validate that SQL is a single safe SELECT-style query."""
    text = sql.strip()
    if not text:
        raise ValueError("SQL is empty")

    parsed = _parse_sql_candidate(text)

    if not isinstance(parsed, exp.Select):
        raise ValueError("Only SELECT queries are allowed")

    if _has_forbidden_expression(parsed):
        raise ValueError("Only SELECT queries are allowed")

    cte_names = _collect_cte_names(parsed)
    for table in parsed.find_all(exp.Table):
        table_name = _extract_table_name(table)
        if not table_name or table_name in cte_names:
            continue

        schema_name = _extract_schema_name(table)
        if schema_name in SYSTEM_SCHEMAS:
            raise ValueError("Only business tables are allowed")
        if schema_name and schema_name != "public":
            raise ValueError("Only business tables are allowed")
        if table_name not in ALLOWED_TABLES:
            raise ValueError("Only business tables are allowed")


def ensure_limit(sql: str, limit: int = 100) -> str:
    """Append a LIMIT clause when the SQL does not already contain one."""
    text = sql.strip()
    if not text:
        return text

    try:
        parsed = sqlglot.parse_one(text, dialect="postgres")
        if parsed.find(exp.Limit):
            return _normalize_sql_text(text)

        # Prefer AST mutation so the output stays valid for common SELECT forms.
        limited = parsed.limit(limit)
        if limited is not None:
            return _normalize_sql_text(limited.sql(dialect="postgres"))
    except Exception:
        pass

    # Fallback for simple SELECTs when AST rewriting is not available.
    normalized = text.rstrip().rstrip(";").rstrip()
    return f"{normalized} LIMIT {limit};" if normalized else normalized
