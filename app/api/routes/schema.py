from fastapi import APIRouter, HTTPException

from app.schemas.schema import SchemaSearchRequest
from app.services.schema_retriever_service import retrieve_schema
from app.services.schema_service import get_database_schema

router = APIRouter()


@router.get("/schema/list")
def list_schema():
    try:
        return {"tables": get_database_schema()}
    except Exception:
        # 不把底层异常细节直接暴露给前端，避免泄露内部信息。
        raise HTTPException(status_code=500, detail="Failed to load database schema.")


@router.post("/schema/search")
def search_schema(request: SchemaSearchRequest):
    try:
        return retrieve_schema(request.question, request.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
