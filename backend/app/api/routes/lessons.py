from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.lesson import Lesson
from app.models.module import CourseModule
from app.models.user import User
from app.schemas.lesson import (
    LessonCreate,
    LessonDetailResponse,
    LessonResponse,
)
from app.services.access_service import (
    ensure_can_manage_course,
    ensure_can_view_course_content,
    get_course_or_404,
)


router = APIRouter(tags=["Lessons"])


def _get_module_or_404(db: Session, module_id: int) -> CourseModule:
    module = db.get(CourseModule, module_id)

    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )

    return module


@router.post(
    "/modules/{module_id}/lessons",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_lesson(
    module_id: int,
    lesson_data: LessonCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    module = _get_module_or_404(db, module_id)
    course = get_course_or_404(db, module.course_id)
    ensure_can_manage_course(course, current_user)

    lesson = Lesson(
        title=lesson_data.title,
        content=lesson_data.content,
        video_url=(
            str(lesson_data.video_url) if lesson_data.video_url else None
        ),
        order=lesson_data.order,
        module_id=module_id,
    )

    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return lesson


@router.get(
    "/modules/{module_id}/lessons",
    response_model=list[LessonResponse],
)
def get_lessons(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    module = _get_module_or_404(db, module_id)
    course = get_course_or_404(db, module.course_id)
    ensure_can_view_course_content(db, course, current_user)

    statement = (
        select(Lesson)
        .where(Lesson.module_id == module_id)
        .order_by(Lesson.order, Lesson.id)
    )

    return list(db.scalars(statement).all())


@router.get(
    "/lessons/{lesson_id}",
    response_model=LessonDetailResponse,
)
def get_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lesson = db.get(Lesson, lesson_id)

    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    module = _get_module_or_404(db, lesson.module_id)
    course = get_course_or_404(db, module.course_id)
    ensure_can_view_course_content(db, course, current_user)

    return LessonDetailResponse(
        id=lesson.id,
        title=lesson.title,
        content=lesson.content,
        video_url=lesson.video_url,
        order=lesson.order,
        module_id=lesson.module_id,
        course_id=course.id,
    )
