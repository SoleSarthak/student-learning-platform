from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.database import get_db
from app.models.course import Course
from app.models.module import CourseModule
from app.models.user import User
from app.schemas.module import ModuleCreate, ModuleResponse


router = APIRouter(
    prefix="/courses",
    tags=["Modules"]
)


@router.post(
    "/{course_id}/modules",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED
)
def create_module(
    course_id: int,
    module_data: ModuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    course = db.get(Course, course_id)

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    if (
        current_user.role != "admin"
        and course.instructor_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You do not own this course"
        )

    module = CourseModule(
        title=module_data.title,
        order=module_data.order,
        course_id=course_id
    )

    db.add(module)
    db.commit()
    db.refresh(module)

    return module


@router.get(
    "/{course_id}/modules",
    response_model=list[ModuleResponse]
)
def get_modules(
    course_id: int,
    db: Session = Depends(get_db)
):

    course = db.get(Course, course_id)

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    statement = (
        select(CourseModule)
        .where(CourseModule.course_id == course_id)
        .order_by(CourseModule.order)
    )

    return list(db.scalars(statement).all())