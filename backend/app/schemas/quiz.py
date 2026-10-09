from pydantic import BaseModel, ConfigDict


class QuizCreate(BaseModel):
    title: str
    passing_score: int = 60


class QuizResponse(BaseModel):
    id: int
    title: str
    passing_score: int
    course_id: int

    model_config = ConfigDict(
        from_attributes=True
    )