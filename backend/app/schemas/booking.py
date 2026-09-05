from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BookingEventType, BookingStatus


class BookingCreate(BaseModel):
    session_id: UUID
    member_id: UUID


class AttendanceUpdate(BaseModel):
    status: BookingStatus


class BookingNoteCreate(BaseModel):
    note: str = Field(min_length=1, max_length=2000)


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

class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int
    page: int
    page_size: int
    pages: int


class RecurrenceCreate(BaseModel):
    class_id: UUID
    start_date: date
    end_date: date
    weekdays: list[int] = Field(min_length=1, max_length=7)
    start_time: time
    primary_instructor_id: UUID
    room_id: UUID
    duration_minutes: int | None = Field(default=None, gt=0, le=480)
    capacity: int | None = Field(default=None, gt=0, le=1000)


class RecurrenceResult(BaseModel):
    created_session_ids: list[UUID]
    created_count: int
    skipped: list[dict[str, str]]


class DashboardResponse(BaseModel):
    sessions_today: int
    bookings_today: int
    no_shows_this_week: int
    currently_waitlisted: int
    currently_waitlisted_members: list[dict[str, str | int]] = Field(default_factory=list)
    booking_breakdown_by_status: dict[str, int]
    booking_breakdown_by_class: dict[str, int]
    attendance_last_eight_weeks: list[dict[str, int | str]]


class MembershipAlertResponse(BaseModel):
    member_id: UUID
    member_name: str
    member_email: str
    membership_expiry: date
    days_remaining: int