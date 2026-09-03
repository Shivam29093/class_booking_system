from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import BookingStatus


class BookingCreate(BaseModel):
    session_id: UUID
    member_id: UUID


class BookingResponse(BaseModel):
    id: UUID
    session_id: UUID
    member_id: UUID
    status: BookingStatus
    booked_at: datetime

    model_config = ConfigDict(from_attributes=True)