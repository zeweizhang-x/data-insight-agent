from __future__ import annotations

import hashlib
import json
from typing import Any

from app.core.redis_client import get_redis_client


def make_cache_key(prefix: str, payload: dict) -> str:
    """Build a stable cache key from a prefix and payload."""
    serialized_payload = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    digest = hashlib.sha256(serialized_payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def get_json_cache(key: str) -> dict | list | None:
    """Read and decode a JSON cache value."""
    try:
        cached_value = get_redis_client().get(key)
        if cached_value is None:
            return None
        return json.loads(cached_value)
    except Exception:
        return None


def set_json_cache(key: str, value: Any, ttl_seconds: int = 3600) -> None:
    """Store a JSON-serializable value in Redis without affecting the main flow."""
    try:
        serialized_value = json.dumps(value, ensure_ascii=False, default=str)
        get_redis_client().set(key, serialized_value, ex=ttl_seconds)
    except Exception:
        return


def delete_cache(key: str) -> None:
    """Delete a cache entry if it exists."""
    try:
        get_redis_client().delete(key)
    except Exception:
        return
