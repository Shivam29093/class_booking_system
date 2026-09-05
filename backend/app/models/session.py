import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Time,
    Column,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


session_instructors = Table(
    "session_instructors",
    Base.metadata,
    Column(
        "session_id",
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "instructor_id",
        UUID(as_uuid=True),
        ForeignKey("instructors.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class ClassSession(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id"),
        nullable=False,
        index=True,
    )

    session_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    primary_instructor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instructors.id"),
        nullable=False,
    )

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id"),
        nullable=False,
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    class_definition: Mapped["ClassModel"] = relationship(
        back_populates="sessions",
    )

    primary_instructor: Mapped["Instructor"] = relationship(
        back_populates="primary_sessions",
        foreign_keys=[primary_instructor_id],
    )

    room: Mapped["Room"] = relationship(
        back_populates="sessions",
    )

    instructors: Mapped[list["Instructor"]] = relationship(
        secondary=session_instructors,
        back_populates="sessions",
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="session",
    )

    @property
    def co_instructor_ids(self) -> list[uuid.UUID]:
        return [instructor.id for instructor in self.instructors]