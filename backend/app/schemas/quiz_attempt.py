from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Answer(BaseModel):
    question_id: int
    answer: str


class QuizSubmit(BaseModel):
    answers: list[Answer]


class QuizResult(BaseModel):
    attempt_id: int
    score: int
    total_questions: int
    percentage: float
    passed: bool
    attempted_at: datetime


class QuizAttemptResponse(BaseModel):
    id: int
    student_id: int
    quiz_id: int
    score: int
    total_questions: int
    passed: bool
    attempted_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )