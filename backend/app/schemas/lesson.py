from pydantic import BaseModel, ConfigDict


class LessonCreate(BaseModel):
    title: str
    content: str
    video_url: str | None = None
    order: int


class LessonResponse(BaseModel):
    id: int
    title: str
    content: str
    video_url: str | None
    order: int
    module_id: int

    model_config = ConfigDict(
        from_attributes=True
    )