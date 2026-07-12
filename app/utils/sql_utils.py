from __future__ import annotations

import re


def extract_sql_from_llm_output(output: str) -> str:
    """Extract SQL from raw LLM output and normalize trailing semicolons."""
    text = output.strip()

    code_block_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if code_block_match:
        text = code_block_match.group(1).strip()

    text = text.rstrip().rstrip(";").rstrip()
    return f"{text};" if text else text


def validate_select_sql(sql: str) -> None:
    """Validate that SQL is a single safe SELECT-style query."""
    text = sql.strip()
    if not text:
        raise ValueError("SQL is empty")

    if text.count(";") > 1:
        raise ValueError("Multiple SQL statements are not allowed")

    normalized = text.lstrip().lower()
    if not (normalized.startswith("select") or normalized.startswith("with")):
        raise ValueError("Only SELECT or WITH queries are allowed")

    forbidden_keywords = (
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "grant",
        "revoke",
    )
    lowered = text.lower()
    for keyword in forbidden_keywords:
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
            raise ValueError(f"Forbidden SQL keyword detected: {keyword.upper()}")


def ensure_limit(sql: str, limit: int = 100) -> str:
    """Append a LIMIT clause when the SQL does not already contain one."""
    text = sql.strip()
    if re.search(r"\blimit\b", text, flags=re.IGNORECASE):
        normalized = text.rstrip().rstrip(";").rstrip()
        return f"{normalized};" if normalized else normalized

    text = text.rstrip().rstrip(";").rstrip()
    return f"{text} LIMIT {limit};" if text else text
