"""Shared permission helpers used by the route modules."""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import User


STAFF_ROLES = ("instructor", "admin")


def get_course_or_404(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    return course


def can_manage_course(course: Course, user: User) -> bool:
    return user.role == "admin" or course.instructor_id == user.id


def ensure_can_manage_course(course: Course, user: User) -> None:
    if not can_manage_course(course, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this course",
        )


def is_enrolled(db: Session, student_id: int, course_id: int) -> bool:
    enrollment = db.scalar(
        select(Enrollment.id).where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
        )
    )
    return enrollment is not None


def ensure_enrolled(db: Session, student_id: int, course_id: int) -> None:
    if not is_enrolled(db, student_id, course_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course",
        )


def ensure_can_view_course_content(
    db: Session, course: Course, user: User
) -> None:
    """Lessons and quiz questions are visible to the course owner, admins
    and enrolled students only."""
    if can_manage_course(course, user):
        return

    ensure_enrolled(db, user.id, course.id)
