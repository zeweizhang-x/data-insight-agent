from __future__ import annotations

from functools import lru_cache

import redis

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    settings = get_settings()
    redis_url = settings.REDIS_URL.strip()
    return redis.Redis.from_url(redis_url, decode_responses=True)


def ping_redis() -> bool:
    try:
        return bool(get_redis_client().ping())
    except Exception:
        return False
