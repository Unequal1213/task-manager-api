from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_completed: bool | None = None

    @model_validator(mode="after")
    def validate_non_nullable_fields(self) -> "TaskUpdate":
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("title cannot be null")
        if (
            "is_completed" in self.model_fields_set
            and self.is_completed is None
        ):
            raise ValueError("is_completed cannot be null")
        return self


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    user_id: int
