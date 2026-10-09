from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.database import get_db
from app.models.certificate import Certificate
from app.models.user import User
from app.schemas.certificate import CertificateResponse


router = APIRouter(
    prefix="/certificates",
    tags=["Certificates"]
)


@router.get(
    "",
    response_model=list[CertificateResponse]
)
def get_my_certificates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    statement = (
        select(Certificate)
        .where(
            Certificate.student_id == current_user.id
        )
        .order_by(
            Certificate.issued_at.desc()
        )
    )

    return list(db.scalars(statement).all())


@router.get(
    "/{certificate_number}",
    response_model=CertificateResponse
)
def get_certificate(
    certificate_number: str,
    db: Session = Depends(get_db)
):

    certificate = db.scalar(
        select(Certificate).where(
            Certificate.certificate_number
            == certificate_number
        )
    )

    if certificate is None:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found"
        )

    return certificate