from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.lesson import Lesson
from app.models.module import CourseModule
from app.models.progress import LessonProgress


def get_course_progress(
    db: Session,
    student_id: int,
    course_id: int,
) -> dict:
    total_lessons = (
        db.scalar(
            select(func.count(Lesson.id))
            .join(CourseModule, Lesson.module_id == CourseModule.id)
            .where(CourseModule.course_id == course_id)
        )
        or 0
    )

    completed_lesson_ids = list(
        db.scalars(
            select(LessonProgress.lesson_id)
            .join(Lesson, LessonProgress.lesson_id == Lesson.id)
            .join(CourseModule, Lesson.module_id == CourseModule.id)
            .where(
                LessonProgress.student_id == student_id,
                LessonProgress.completed.is_(True),
                CourseModule.course_id == course_id,
            )
            .order_by(LessonProgress.lesson_id)
        ).all()
    )

    completed_lessons = len(completed_lesson_ids)

    percentage = 0.0
    if total_lessons > 0:
        percentage = round(
            min(completed_lessons / total_lessons, 1) * 100,
            2,
        )

    return {
        "course_id": course_id,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "progress_percentage": percentage,
        "completed_lesson_ids": completed_lesson_ids,
    }
