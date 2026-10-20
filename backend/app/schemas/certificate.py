from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CertificateResponse(BaseModel):
    id: int
    certificate_number: str
    student_id: int
    course_id: int
    course_title: str
    issued_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CertificateVerification(BaseModel):
    """Public view used to verify a certificate - no internal ids."""

    valid: bool = True
    certificate_number: str
    student_name: str
    course_title: str
    issued_at: datetime

    model_config = ConfigDict(from_attributes=True)
