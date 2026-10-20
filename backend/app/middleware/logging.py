import logging
import time
import uuid

from fastapi import Request


logger = logging.getLogger("api")


async def request_logging_middleware(request: Request, call_next):
    # A short id lets you match a user's error report to the exact log lines.
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]

    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "[%s] %s %s -> %s | %.4fs",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    return response
