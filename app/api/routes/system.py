from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.redis_client import get_redis_client, ping_redis
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


@router.get("/system/cache/stats")
def system_cache_stats() -> dict:
    try:
        redis_client = get_redis_client()
        text2sql_cache_keys = _count_cache_keys(redis_client, "text2sql:")
        schema_retrieval_cache_keys = _count_cache_keys(redis_client, "schema_retrieval:")
        return {
            "redis": True,
            "text2sql_cache_keys": text2sql_cache_keys,
            "schema_retrieval_cache_keys": schema_retrieval_cache_keys,
        }
    except Exception:
        return {
            "redis": False,
            "text2sql_cache_keys": 0,
            "schema_retrieval_cache_keys": 0,
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


def _count_cache_keys(redis_client, prefix: str) -> int:
    count = 0
    for _key in redis_client.scan_iter(match=f"{prefix}*"):
        count += 1
    return count
