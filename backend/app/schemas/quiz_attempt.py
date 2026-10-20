from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Answer(BaseModel):
    question_id: int
    answer: Literal["A", "B", "C", "D"]

    @field_validator("answer", mode="before")
    @classmethod
    def uppercase_answer(cls, value):
        return value.upper() if isinstance(value, str) else value


class QuizSubmit(BaseModel):
    answers: list[Answer] = Field(max_length=200)


class QuizResult(BaseModel):
    attempt_id: int
    score: int
    total_questions: int
    percentage: float
    passed: bool
    attempted_at: datetime
    certificate_issued: bool = False
    certificate_number: str | None = None
    lessons_remaining: int = 0


class QuizAttemptResponse(BaseModel):
    id: int
    student_id: int
    quiz_id: int
    score: int
    total_questions: int
    passed: bool
    attempted_at: datetime

    model_config = ConfigDict(from_attributes=True)
