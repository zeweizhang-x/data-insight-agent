from sqlalchemy import text

from app.db.session import SessionLocal

MAX_ROWS = 100


def execute_select_sql(sql: str) -> dict:
    normalized_sql = sql.strip()
    if not normalized_sql:
        raise ValueError("SQL cannot be empty")

    # 只允许 SELECT 查询，避免把这个调试接口误用成写操作入口。
    if not normalized_sql.lower().startswith("select"):
        raise ValueError("Only SELECT statements are allowed")

    session = SessionLocal()
    try:
        result = session.execute(text(normalized_sql))
        columns = list(result.keys())
        rows = [dict(row._mapping) for row in result.fetchmany(MAX_ROWS)]
        return {"columns": columns, "rows": rows}
    finally:
        session.close()
