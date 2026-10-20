"""Tiny Redis cache helpers that FAIL OPEN.

If Redis is down, the API keeps working (just slower) instead of returning 500.
"""
import json
import logging
from typing import Any

from app.db.redis import redis_client


logger = logging.getLogger(__name__)


def cache_get_json(key: str) -> Any | None:
    try:
        raw = redis_client.get(key)
        return json.loads(raw) if raw else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cache read failed for %s: %s", key, exc)
        return None


def cache_set_json(key: str, value: Any, ttl_seconds: int) -> None:
    try:
        redis_client.setex(key, ttl_seconds, json.dumps(value))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cache write failed for %s: %s", key, exc)


def cache_delete_prefix(prefix: str) -> None:
    try:
        for key in redis_client.scan_iter(match=f"{prefix}*"):
            redis_client.delete(key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cache invalidation failed for %s: %s", prefix, exc)
