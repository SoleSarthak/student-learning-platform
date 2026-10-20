from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.lesson import Lesson
from app.models.module import CourseModule
from app.models.progress import LessonProgress
from app.models.user import User
from app.schemas.progress import LessonCompleteResponse, ProgressResponse
from app.services.access_service import ensure_enrolled
from app.services.certificate_service import issue_certificate_if_eligible
from app.services.progress_service import get_course_progress


router = APIRouter(
    prefix="/progress",
    tags=["Progress"],
)


def _find_progress(
    db: Session,
    student_id: int,
    lesson_id: int,
) -> LessonProgress | None:
    return db.scalar(
        select(LessonProgress).where(
            LessonProgress.student_id == student_id,
            LessonProgress.lesson_id == lesson_id,
        )
    )


@router.post(
    "/lessons/{lesson_id}/complete",
    response_model=LessonCompleteResponse,
)
def complete_lesson(
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

    module = db.get(CourseModule, lesson.module_id)

    ensure_enrolled(db, current_user.id, module.course_id)

    progress = _find_progress(db, current_user.id, lesson_id)

    if progress is None:
        progress = LessonProgress(
            student_id=current_user.id,
            lesson_id=lesson_id,
            completed=True,
            completed_at=datetime.now(timezone.utc),
        )

        db.add(progress)

        try:
            db.commit()
        except IntegrityError:
            # Double-click / two tabs: the row already exists. That is fine.
            db.rollback()
            progress = _find_progress(db, current_user.id, lesson_id)

    elif not progress.completed:
        progress.completed = True
        progress.completed_at = datetime.now(timezone.utc)
        db.commit()

    db.refresh(progress)

    # Finishing the last lesson may complete the course.
    certificate, _created = issue_certificate_if_eligible(
        db,
        current_user,
        module.course_id,
    )

    return {
        "lesson_id": lesson_id,
        "completed": progress.completed,
        "completed_at": progress.completed_at,
        "certificate_number": (
            certificate.certificate_number if certificate else None
        ),
    }


@router.get(
    "/courses/{course_id}",
    response_model=ProgressResponse,
)
def get_progress_for_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_enrolled(db, current_user.id, course_id)

    return get_course_progress(db, current_user.id, course_id)
