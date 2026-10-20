from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.module import CourseModule
from app.models.user import User
from app.schemas.module import ModuleCreate, ModuleResponse
from app.services.access_service import (
    ensure_can_manage_course,
    get_course_or_404,
)


router = APIRouter(
    prefix="/courses",
    tags=["Modules"],
)


@router.post(
    "/{course_id}/modules",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_module(
    course_id: int,
    module_data: ModuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = get_course_or_404(db, course_id)
    ensure_can_manage_course(course, current_user)

    module = CourseModule(
        title=module_data.title,
        order=module_data.order,
        course_id=course_id,
    )

    db.add(module)
    db.commit()
    db.refresh(module)

    return module


@router.get(
    "/{course_id}/modules",
    response_model=list[ModuleResponse],
)
def get_modules(
    course_id: int,
    db: Session = Depends(get_db),
):
    get_course_or_404(db, course_id)

    statement = (
        select(CourseModule)
        .where(CourseModule.course_id == course_id)
        .order_by(CourseModule.order, CourseModule.id)
    )

    return list(db.scalars(statement).all())
