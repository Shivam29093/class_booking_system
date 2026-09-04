from datetime import datetime
from uuid import UUID
from app.models.enums import BookingEventType

from pydantic import BaseModel, ConfigDict

from app.models.enums import BookingStatus


class BookingCreate(BaseModel):
    session_id: UUID
    member_id: UUID


class AttendanceUpdate(BaseModel):
    status: BookingStatus


class BookingResponse(BaseModel):
    id: UUID
    session_id: UUID
    member_id: UUID
    status: BookingStatus
    booked_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BookingHistoryResponse(BaseModel):
    id: UUID
    booking_id: UUID
    event_type: BookingEventType
    old_status: BookingStatus | None
    new_status: BookingStatus | None
    note: str | None
    changed_by_user_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)    