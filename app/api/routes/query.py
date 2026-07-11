from fastapi import APIRouter, HTTPException

from app.schemas.query import RawSqlRequest
from app.services.query_service import execute_select_sql

router = APIRouter()


@router.post("/query/raw-sql")
def raw_sql_query(payload: RawSqlRequest):
    sql = payload.sql.strip()
    if not sql:
        raise HTTPException(status_code=400, detail="SQL cannot be empty")

    try:
        return execute_select_sql(sql)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        # 避免把数据库底层异常直接暴露给调用方。
        raise HTTPException(status_code=500, detail="Failed to execute SQL query.")
