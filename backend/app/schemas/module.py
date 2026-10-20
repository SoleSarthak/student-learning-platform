from pydantic import BaseModel, ConfigDict, Field


class ModuleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    order: int = Field(ge=0, le=10000)


class ModuleResponse(BaseModel):
    id: int
    title: str
    order: int
    course_id: int

    model_config = ConfigDict(from_attributes=True)
