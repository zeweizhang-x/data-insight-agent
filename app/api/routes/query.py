from fastapi import APIRouter, HTTPException

from app.schemas.query import RawSqlRequest, TextToSqlRequest
from app.services.query_service import execute_select_sql
from app.services.text2sql_service import answer_question_with_sql

router = APIRouter()


def _brief_error_detail(error: Exception) -> str:
    """Return a short, user-facing error message."""
    message = str(error).strip() or "Request failed"
    return message[:200]


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


@router.post("/query/text-to-sql")
def text_to_sql_query(payload: TextToSqlRequest):
    try:
        return answer_question_with_sql(payload.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=_brief_error_detail(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=_brief_error_detail(exc))
