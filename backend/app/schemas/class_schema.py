from uuid import UUID

from pydantic import BaseModel, Field


class ClassCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1)
    discipline: str = Field(min_length=1, max_length=100)
    default_duration_minutes: int = Field(gt=0, le=480)
    default_capacity: int = Field(gt=0, le=1000)


class ClassUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, min_length=1)
    discipline: str | None = Field(default=None, min_length=1, max_length=100)
    default_duration_minutes: int | None = Field(
        default=None,
        gt=0,
        le=480,
    )
    default_capacity: int | None = Field(
        default=None,
        gt=0,
        le=1000,
    )


class ClassResponse(BaseModel):
    id: UUID
    title: str
    description: str
    discipline: str
    default_duration_minutes: int
    default_capacity: int
    is_archived: bool

    model_config = {
        "from_attributes": True
    }