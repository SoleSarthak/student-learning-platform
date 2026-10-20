import logging

from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.db.redis import redis_client


logger = logging.getLogger(__name__)


def rate_limit(scope: str, limit: int, window_seconds: int):
    """FastAPI dependency: allow `limit` calls per `window_seconds` per client IP.

    Uses a Redis counter. If Redis is down we fail OPEN (allow the request)
    so an infrastructure problem never locks every user out.

    Note: behind a reverse proxy, configure the proxy / uvicorn
    (--proxy-headers) so request.client is the real client IP.
    """

    def dependency(request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{scope}:{client_ip}"

        try:
            count = redis_client.incr(key)
            if count == 1:
                redis_client.expire(key, window_seconds)
        except Exception as exc:  # noqa: BLE001 - fail open on any Redis error
            logger.warning("Rate limiter unavailable: %s", exc)
            return

        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Please try again in a minute.",
                headers={"Retry-After": str(window_seconds)},
            )

    return dependency
