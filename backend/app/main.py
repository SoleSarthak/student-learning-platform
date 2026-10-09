import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text

from app.api.routes.auth import router as auth_router
from app.api.routes.courses import router as courses_router
from app.api.routes.modules import router as modules_router
from app.api.routes.lessons import router as lessons_router
from app.api.routes.enrollments import router as enrollments_router
from app.api.routes.progress import router as progress_router
from app.api.routes.quizzes import router as quizzes_router
from app.api.routes.certificates import router as certificates_router

from app.db.database import engine
from app.db.redis import redis_client

from app.core.logging_config import setup_logging

from app.exceptions.handlers import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)

from app.middleware.logging import request_logging_middleware


# Import all models so SQLAlchemy/Alembic knows about them
from app.models.user import User
from app.models.course import Course
from app.models.module import CourseModule
from app.models.lesson import Lesson
from app.models.enrollment import Enrollment
from app.models.progress import LessonProgress
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.quiz_attempt import QuizAttempt
from app.models.certificate import Certificate


# --------------------------------------------------
# Logging
# --------------------------------------------------

setup_logging()

logger = logging.getLogger(__name__)


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="Student Learning Platform API",
    description="Backend API for a student learning platform",
    version="1.0.0",
)


# --------------------------------------------------
# Exception handlers
# --------------------------------------------------

app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    Exception,
    general_exception_handler,
)


# --------------------------------------------------
# Middleware
# --------------------------------------------------

app.middleware("http")(request_logging_middleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# API routes
# --------------------------------------------------

app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    courses_router,
    prefix="/api/v1",
)

app.include_router(
    modules_router,
    prefix="/api/v1",
)

app.include_router(
    lessons_router,
    prefix="/api/v1",
)

app.include_router(
    enrollments_router,
    prefix="/api/v1",
)

app.include_router(
    progress_router,
    prefix="/api/v1",
)

app.include_router(
    quizzes_router,
    prefix="/api/v1",
)

app.include_router(
    certificates_router,
    prefix="/api/v1",
)


# --------------------------------------------------
# Root
# --------------------------------------------------

@app.get("/")
def root():

    return {
        "message": "Student Learning Platform API",
        "version": "1.0.0",
    }


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/health")
def health_check():

    database_status = "disconnected"
    redis_status = "disconnected"

    # PostgreSQL
    try:

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        database_status = "connected"

    except Exception as exc:

        logger.error(
            "Database health check failed: %s",
            exc,
        )

    # Redis
    try:

        redis_client.ping()

        redis_status = "connected"

    except Exception as exc:

        logger.error(
            "Redis health check failed: %s",
            exc,
        )

    return {
        "status": "ok",
        "database": database_status,
        "redis": redis_status,
    }