from datetime import date
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class MemberCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    membership_expiry: date


class MemberUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    membership_expiry: date | None = None


class MemberResponse(BaseModel):
    id: UUID
    name: str
    email: str
    membership_expiry: date

    model_config = {
        "from_attributes": True
    }