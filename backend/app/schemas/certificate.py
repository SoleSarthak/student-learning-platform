from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CertificateResponse(BaseModel):
    id: int
    certificate_number: str
    student_id: int
    course_id: int
    issued_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )