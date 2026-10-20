import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes.auth import router as auth_router
from app.api.routes.certificates import router as certificates_router
from app.api.routes.courses import router as courses_router
from app.api.routes.enrollments import router as enrollments_router
from app.api.routes.lessons import router as lessons_router
from app.api.routes.modules import router as modules_router
from app.api.routes.progress import router as progress_router
from app.api.routes.quizzes import router as quizzes_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.database import engine
from app.db.redis import redis_client
from app.exceptions.handlers import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.middleware.logging import request_logging_middleware

# Import all models so SQLAlchemy/Alembic know about every table.
from app.models import (  # noqa: F401
    certificate,
    course,
    enrollment,
    lesson,
    module,
    progress,
    question,
    quiz,
    quiz_attempt,
    user,
)


setup_logging()

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Student Learning Platform API",
    description=(
        "Courses, lessons, quizzes, progress tracking and certificates."
    ),
    version="1.0.0",
)


# --------------------------------------------------
# Exception handlers
# --------------------------------------------------

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# --------------------------------------------------
# Middleware (added last = runs first, so CORS wraps everything)
# --------------------------------------------------

app.middleware("http")(request_logging_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


# --------------------------------------------------
# API routes
# --------------------------------------------------

API_PREFIX = "/api/v1"
print("finding router router")
for router in (
    auth_router,
    courses_router,
    modules_router,
    lessons_router,
    enrollments_router,
    progress_router,
    quizzes_router,
    certificates_router,
):
    app.include_router(router, prefix=API_PREFIX)


# --------------------------------------------------
# Root + health
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Student Learning Platform API",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    """Used by Docker / load balancers / uptime monitors.

    Returns 200 only when PostgreSQL AND Redis are reachable, otherwise 503,
    so an orchestrator knows to stop sending traffic to a broken instance.
    """
    database_status = "disconnected"
    redis_status = "disconnected"

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        database_status = "connected"

    except Exception as exc:  # noqa: BLE001
        logger.error("Database health check failed: %s", exc)

    try:
        redis_client.ping()
        redis_status = "connected"

    except Exception as exc:  # noqa: BLE001
        logger.error("Redis health check failed: %s", exc)

    healthy = database_status == "connected" and redis_status == "connected"

    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "ok" if healthy else "degraded",
            "database": database_status,
            "redis": redis_status,
        },
    )
