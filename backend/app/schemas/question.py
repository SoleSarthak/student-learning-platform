from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuestionCreate(BaseModel):
    question_text: str = Field(min_length=1, max_length=1000)
    option_a: str = Field(min_length=1, max_length=500)
    option_b: str = Field(min_length=1, max_length=500)
    option_c: str = Field(min_length=1, max_length=500)
    option_d: str = Field(min_length=1, max_length=500)
    correct_answer: Literal["A", "B", "C", "D"]

    @field_validator("correct_answer", mode="before")
    @classmethod
    def uppercase_answer(cls, value):
        return value.upper() if isinstance(value, str) else value


# NOTE: deliberately has NO `correct_answer` field - students must never
# receive the answer key.
class QuestionResponse(BaseModel):
    id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    quiz_id: int

    model_config = ConfigDict(from_attributes=True)
