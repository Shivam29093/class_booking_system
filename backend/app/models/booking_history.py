import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BookingEventType, BookingStatus


class BookingHistory(Base):
    __tablename__ = "booking_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[BookingEventType] = mapped_column(
        String(20),
        nullable=False,
    )

    old_status: Mapped[BookingStatus | None] = mapped_column(
        String(20),
        nullable=True,
    )

    new_status: Mapped[BookingStatus | None] = mapped_column(
        String(20),
        nullable=True,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    booking: Mapped["Booking"] = relationship(
        back_populates="history",
    )

    changed_by: Mapped["User | None"] = relationship()