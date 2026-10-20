from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_instructor
from app.db.database import get_db
from app.models.course import Course
from app.models.module import CourseModule
from app.models.user import User
from app.schemas.course import (
    CourseCreate,
    CourseResponse,
    CourseUpdate,
    ModuleOutline,
)
from app.schemas.lesson import LessonSummary
from app.services.access_service import (
    ensure_can_manage_course,
    get_course_or_404,
)
from app.services.cache import (
    cache_delete_prefix,
    cache_get_json,
    cache_set_json,
)


router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


COURSES_CACHE_PREFIX = "courses:list:"
COURSES_CACHE_TTL = 60


def _escape_like(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    course = Course(
        title=course_data.title,
        description=course_data.description,
        difficulty=course_data.difficulty,
        instructor_id=current_user.id,
    )

    db.add(course)
    db.commit()
    db.refresh(course)

    cache_delete_prefix(COURSES_CACHE_PREFIX)

    return course


@router.get("", response_model=list[CourseResponse])
def get_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
):
    search = q.strip() if q else None

    # Only the plain (un-searched) list is cached.
    cache_key = None

    if not search:
        cache_key = f"{COURSES_CACHE_PREFIX}{skip}:{limit}"
        cached = cache_get_json(cache_key)

        if cached is not None:
            return cached

    statement = select(Course).order_by(
        Course.created_at.desc(),
        Course.id.desc(),
    )

    if search:
        pattern = f"%{_escape_like(search)}%"
        statement = statement.where(
            or_(
                Course.title.ilike(pattern, escape="\\"),
                Course.description.ilike(pattern, escape="\\"),
            )
        )

    courses = db.scalars(statement.offset(skip).limit(limit)).all()

    payload = [
        CourseResponse.model_validate(course).model_dump(mode="json")
        for course in courses
    ]

    if cache_key:
        cache_set_json(cache_key, payload, COURSES_CACHE_TTL)

    return payload


# NOTE: "/mine" must be declared BEFORE "/{course_id}", otherwise FastAPI
# would try to read the word "mine" as a course id.
@router.get("/mine", response_model=list[CourseResponse])
def get_my_courses(
    current_user: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    statement = (
        select(Course)
        .where(Course.instructor_id == current_user.id)
        .order_by(Course.created_at.desc(), Course.id.desc())
    )

    return list(db.scalars(statement).all())


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
):
    return get_course_or_404(db, course_id)


@router.get(
    "/{course_id}/outline",
    response_model=list[ModuleOutline],
)
def get_course_outline(
    course_id: int,
    db: Session = Depends(get_db),
):
    """Modules with their lesson titles (no lesson content).

    Public on purpose: it works as the course syllabus. The lesson content
    itself is only available to enrolled students.
    """
    get_course_or_404(db, course_id)

    modules = db.scalars(
        select(CourseModule)
        .where(CourseModule.course_id == course_id)
        .options(selectinload(CourseModule.lessons))
        .order_by(CourseModule.order, CourseModule.id)
    ).all()

    return [
        ModuleOutline(
            id=module.id,
            title=module.title,
            order=module.order,
            course_id=module.course_id,
            lessons=[
                LessonSummary.model_validate(lesson)
                for lesson in sorted(
                    module.lessons,
                    key=lambda item: (item.order, item.id),
                )
            ],
        )
        for module in modules
    ]


@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    course_data: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = get_course_or_404(db, course_id)
    ensure_can_manage_course(course, current_user)

    for field, value in course_data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(course, field, value)

    db.commit()
    db.refresh(course)

    cache_delete_prefix(COURSES_CACHE_PREFIX)

    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = get_course_or_404(db, course_id)
    ensure_can_manage_course(course, current_user)

    db.delete(course)
    db.commit()

    cache_delete_prefix(COURSES_CACHE_PREFIX)
