from functools import lru_cache
from typing import Any

from app.core.config import settings


@lru_cache
def get_redis_client() -> Any:
    """Create the Redis client on first use."""
    import redis

    return redis.from_url(settings.redis_url, decode_responses=True)


def cache_get(key: str):
    """Get value from cache."""
    redis_client = get_redis_client()
    return redis_client.get(key)


def cache_set(key: str, value: str, ttl: int = 3600):
    """Set value in cache with TTL."""
    redis_client = get_redis_client()
    redis_client.setex(key, ttl, value)


def cache_delete(key: str):
    """Delete value from cache."""
    redis_client = get_redis_client()
    redis_client.delete(key)


def cache_clear_pattern(pattern: str):
    """Clear all keys matching pattern."""
    redis_client = get_redis_client()
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)
