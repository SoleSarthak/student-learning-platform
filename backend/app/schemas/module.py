from pydantic import BaseModel, ConfigDict


class ModuleCreate(BaseModel):
    title: str
    order: int


class ModuleResponse(BaseModel):
    id: int
    title: str
    order: int
    course_id: int

    model_config = ConfigDict(
        from_attributes=True
    )