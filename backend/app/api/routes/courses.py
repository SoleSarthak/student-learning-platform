import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.database import get_db
from app.db.redis import redis_client
from app.models.course import Course
from app.models.user import User
from app.schemas.course import CourseCreate, CourseResponse


router = APIRouter(
    prefix="/courses",
    tags=["Courses"]
)


COURSES_CACHE_KEY = "courses:all"
COURSES_CACHE_TTL = 60


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED
)
def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    if current_user.role not in ["instructor", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only instructors and admins can create courses"
        )

    course = Course(
        title=course_data.title,
        description=course_data.description,
        difficulty=course_data.difficulty,
        instructor_id=current_user.id
    )

    db.add(course)
    db.commit()
    db.refresh(course)

    # Invalidate cached course list
    redis_client.delete(COURSES_CACHE_KEY)

    return course


@router.get(
    "",
    response_model=list[CourseResponse]
)
def get_courses(
    db: Session = Depends(get_db)
):

    # -----------------------------------------
    # Check Redis cache
    # -----------------------------------------

    cached_courses = redis_client.get(COURSES_CACHE_KEY)

    if cached_courses:
        return json.loads(cached_courses)

    # -----------------------------------------
    # Query PostgreSQL
    # -----------------------------------------

    statement = select(Course).order_by(
        Course.created_at.desc()
    )

    courses = list(db.scalars(statement).all())

    # -----------------------------------------
    # Convert SQLAlchemy objects to JSON
    # -----------------------------------------

    course_data = [
        {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "difficulty": course.difficulty,
            "instructor_id": course.instructor_id,
            "created_at": course.created_at.isoformat(),
        }
        for course in courses
    ]

    # -----------------------------------------
    # Store in Redis for 60 seconds
    # -----------------------------------------

    redis_client.setex(
        COURSES_CACHE_KEY,
        COURSES_CACHE_TTL,
        json.dumps(course_data)
    )

    return course_data


@router.get(
    "/{course_id}",
    response_model=CourseResponse
)
def get_course(
    course_id: int,
    db: Session = Depends(get_db)
):

    course = db.get(Course, course_id)

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    return course