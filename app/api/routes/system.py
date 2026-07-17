from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.redis_client import ping_redis
from app.db.session import SessionLocal
from app.rag.vector_store import get_schema_collection

router = APIRouter()


@router.get("/system/health")
def system_health_check() -> dict:
    postgres_ok = _check_postgres()
    redis_ok = ping_redis()
    chroma_ok = _check_chroma()

    status = "ok" if postgres_ok and redis_ok and chroma_ok else "degraded"
    return {
        "status": status,
        "checks": {
            "api": True,
            "postgres": postgres_ok,
            "redis": redis_ok,
            "chroma": chroma_ok,
        },
    }


def _check_postgres() -> bool:
    try:
        db = SessionLocal()
        try:
            db.execute(text("select 1"))
            return True
        finally:
            db.close()
    except Exception:
        return False


def _check_chroma() -> bool:
    try:
        collection = get_schema_collection()
        collection.count()
        return True
    except Exception:
        return False
