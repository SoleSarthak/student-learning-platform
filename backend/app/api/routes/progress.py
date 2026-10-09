from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.database import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.module import CourseModule
from app.models.progress import LessonProgress
from app.models.user import User
from app.schemas.progress import (
    LessonCompleteResponse,
    ProgressResponse
)


router = APIRouter(
    prefix="/progress",
    tags=["Progress"]
)


@router.post(
    "/lessons/{lesson_id}/complete",
    response_model=LessonCompleteResponse
)
def complete_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    lesson = db.get(Lesson, lesson_id)

    if lesson is None:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found"
        )

    module = db.get(
        CourseModule,
        lesson.module_id
    )

    enrollment = db.scalar(
        select(Enrollment)
        .join(Course, Enrollment.course_id == Course.id)
        .where(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == module.course_id
        )
    )

    if enrollment is None:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course"
        )

    progress = db.scalar(
        select(LessonProgress).where(
            LessonProgress.student_id == current_user.id,
            LessonProgress.lesson_id == lesson_id
        )
    )

    if progress is None:

        progress = LessonProgress(
            student_id=current_user.id,
            lesson_id=lesson_id,
            completed=True,
            completed_at=datetime.now(timezone.utc)
        )

        db.add(progress)

    else:

        progress.completed = True
        progress.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(progress)

    return progress


@router.get(
    "/courses/{course_id}",
    response_model=ProgressResponse
)
def get_course_progress(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == course_id
        )
    )

    if enrollment is None:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course"
        )

    total_lessons = db.scalar(
        select(func.count(Lesson.id))
        .join(
            CourseModule,
            Lesson.module_id == CourseModule.id
        )
        .where(
            CourseModule.course_id == course_id
        )
    ) or 0

    completed_lessons = db.scalar(
        select(func.count(LessonProgress.id))
        .join(
            Lesson,
            LessonProgress.lesson_id == Lesson.id
        )
        .join(
            CourseModule,
            Lesson.module_id == CourseModule.id
        )
        .where(
            LessonProgress.student_id == current_user.id,
            LessonProgress.completed.is_(True),
            CourseModule.course_id == course_id
        )
    ) or 0

    percentage = 0.0

    if total_lessons > 0:
        percentage = round(
            (completed_lessons / total_lessons) * 100,
            2
        )

    return {
        "course_id": course_id,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "progress_percentage": percentage
    }