from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.lesson import LessonSummary


Difficulty = Literal["beginner", "intermediate", "advanced"]


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    difficulty: Difficulty = "beginner"


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    difficulty: Difficulty | None = None


class CourseResponse(BaseModel):
    id: int
    title: str
    description: str
    difficulty: str
    instructor_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModuleOutline(BaseModel):
    id: int
    title: str
    order: int
    course_id: int
    lessons: list[LessonSummary]
