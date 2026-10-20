from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.certificate import Certificate
from app.models.user import User
from app.schemas.certificate import (
    CertificateResponse,
    CertificateVerification,
)


router = APIRouter(
    prefix="/certificates",
    tags=["Certificates"],
)


@router.get("", response_model=list[CertificateResponse])
def get_my_certificates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    statement = (
        select(Certificate)
        .where(Certificate.student_id == current_user.id)
        .options(selectinload(Certificate.course))
        .order_by(Certificate.issued_at.desc(), Certificate.id.desc())
    )

    return list(db.scalars(statement).all())


@router.get(
    "/verify/{certificate_number}",
    response_model=CertificateVerification,
)
def verify_certificate(
    certificate_number: str,
    db: Session = Depends(get_db),
):
    """Public endpoint so an employer can check a certificate is real.
    Only exposes the student's name, course title and date."""
    certificate = db.scalar(
        select(Certificate)
        .where(Certificate.certificate_number == certificate_number)
        .options(
            selectinload(Certificate.course),
            selectinload(Certificate.student),
        )
    )

    if certificate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )

    return certificate
