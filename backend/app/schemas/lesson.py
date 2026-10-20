from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class LessonCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=50000)
    # Only http(s) URLs are accepted, so a stored link can never be a
    # "javascript:" URL.
    video_url: HttpUrl | None = None
    order: int = Field(ge=0, le=10000)


class LessonSummary(BaseModel):
    id: int
    title: str
    order: int

    model_config = ConfigDict(from_attributes=True)


class LessonResponse(BaseModel):
    id: int
    title: str
    content: str
    video_url: str | None
    order: int
    module_id: int

    model_config = ConfigDict(from_attributes=True)


class LessonDetailResponse(LessonResponse):
    course_id: int
