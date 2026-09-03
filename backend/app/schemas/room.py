from uuid import UUID

from pydantic import BaseModel, Field


class RoomCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class RoomUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class RoomResponse(BaseModel):
    id: UUID
    name: str

    model_config = {
        "from_attributes": True
    }