from fastapi import APIRouter, HTTPException

from app.services.schema_service import get_database_schema

router = APIRouter()


@router.get("/schema/list")
def list_schema():
    try:
        return {"tables": get_database_schema()}
    except Exception:
        # 不把底层异常细节直接暴露给前端，避免泄露内部信息。
        raise HTTPException(status_code=500, detail="Failed to load database schema.")
