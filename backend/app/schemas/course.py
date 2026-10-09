from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CourseCreate(BaseModel):
    title: str
    description: str
    difficulty: str = "beginner"


class CourseResponse(BaseModel):
    id: int
    title: str
    description: str
    difficulty: str
    instructor_id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )