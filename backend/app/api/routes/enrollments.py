from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.database import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.enrollment import EnrollmentResponse


router = APIRouter(
    prefix="/enrollments",
    tags=["Enrollments"]
)


@router.post(
    "/courses/{course_id}",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED
)
def enroll_in_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    course = db.get(Course, course_id)

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    existing = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == course_id
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Already enrolled in this course"
        )

    enrollment = Enrollment(
        student_id=current_user.id,
        course_id=course_id
    )

    db.add(enrollment)

    try:
        db.commit()
        db.refresh(enrollment)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Already enrolled in this course"
        )

    return enrollment


@router.get(
    "",
    response_model=list[EnrollmentResponse]
)
def get_my_enrollments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    statement = (
        select(Enrollment)
        .where(
            Enrollment.student_id == current_user.id
        )
        .order_by(Enrollment.enrolled_at.desc())
    )

    return list(db.scalars(statement).all())