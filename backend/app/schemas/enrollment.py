from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    enrolled_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )