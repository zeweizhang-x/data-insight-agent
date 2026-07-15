from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal

MAX_ROWS = 100


def _serialize_value(value: Any) -> Any:
    """Convert common database types into JSON-friendly values."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    return value


def execute_select_sql(sql: str) -> dict:
    normalized_sql = sql.strip()
    if not normalized_sql:
        raise ValueError("SQL cannot be empty")

    # 只允许 SELECT / WITH 查询，避免把这个调试接口误用成写操作入口。
    normalized_lower = normalized_sql.lstrip().lower()
    if not (normalized_lower.startswith("select") or normalized_lower.startswith("with")):
        raise ValueError("Only SELECT statements are allowed")

    session = SessionLocal()
    try:
        result = session.execute(text(normalized_sql))
        columns = list(result.keys())
        rows = [
            _serialize_value(dict(row._mapping))
            for row in result.fetchmany(MAX_ROWS)
        ]
        return {"columns": columns, "rows": rows}
    except SQLAlchemyError as exc:
        session.rollback()
        error_message = str(exc.orig) if getattr(exc, "orig", None) else str(exc)
        raise RuntimeError(f"Database query failed: {error_message[:120]}") from exc
    finally:
        session.close()
