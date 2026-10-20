from pydantic import BaseModel, ConfigDict, Field


class QuizCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    passing_score: int = Field(default=60, ge=0, le=100)


class QuizResponse(BaseModel):
    id: int
    title: str
    passing_score: int
    course_id: int

    model_config = ConfigDict(from_attributes=True)
