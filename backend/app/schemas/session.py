from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    class_id: UUID
    session_date: date
    start_time: time
    primary_instructor_id: UUID
    room_id: UUID
    duration_minutes: int | None = Field(default=None, gt=0)
    capacity: int | None = Field(default=None, gt=0)


class SessionUpdate(BaseModel):
    session_date: date | None = None
    start_time: time | None = None
    primary_instructor_id: UUID | None = None
    room_id: UUID | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    capacity: int | None = Field(default=None, gt=0)


class SessionResponse(BaseModel):
    id: UUID
    class_id: UUID
    session_date: date
    start_time: time
    primary_instructor_id: UUID
    room_id: UUID
    duration_minutes: int
    capacity: int

    class Config:
        from_attributes = True