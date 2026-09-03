from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class InstructorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class InstructorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None


class InstructorResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    email: str

    model_config = {
        "from_attributes": True
    }