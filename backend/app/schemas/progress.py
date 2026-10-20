from datetime import datetime

from pydantic import BaseModel


class ProgressResponse(BaseModel):
    course_id: int
    total_lessons: int
    completed_lessons: int
    progress_percentage: float
    completed_lesson_ids: list[int]


class LessonCompleteResponse(BaseModel):
    lesson_id: int
    completed: bool
    completed_at: datetime | None
    certificate_number: str | None = None
