from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.database import get_db
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.module import CourseModule
from app.models.user import User
from app.schemas.lesson import LessonCreate, LessonResponse


router = APIRouter(
    prefix="/modules",
    tags=["Lessons"]
)


@router.post(
    "/{module_id}/lessons",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED
)
def create_lesson(
    module_id: int,
    lesson_data: LessonCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    module = db.get(CourseModule, module_id)

    if module is None:
        raise HTTPException(
            status_code=404,
            detail="Module not found"
        )

    course = db.get(Course, module.course_id)

    if (
        current_user.role != "admin"
        and course.instructor_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You do not own this course"
        )

    lesson = Lesson(
        title=lesson_data.title,
        content=lesson_data.content,
        video_url=lesson_data.video_url,
        order=lesson_data.order,
        module_id=module_id
    )

    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return lesson


@router.get(
    "/{module_id}/lessons",
    response_model=list[LessonResponse]
)
def get_lessons(
    module_id: int,
    db: Session = Depends(get_db)
):

    module = db.get(CourseModule, module_id)

    if module is None:
        raise HTTPException(
            status_code=404,
            detail="Module not found"
        )

    statement = (
        select(Lesson)
        .where(Lesson.module_id == module_id)
        .order_by(Lesson.order)
    )

    return list(db.scalars(statement).all())