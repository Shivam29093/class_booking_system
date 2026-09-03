import uuid
from app.models.session import session_instructors
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Instructor(Base):
    __tablename__ = "instructors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="instructor",
    )
    @property
    def email(self) -> str:
        return self.user.email
    primary_sessions: Mapped[list["ClassSession"]] = relationship(
        back_populates="primary_instructor",
        foreign_keys="ClassSession.primary_instructor_id",
    )

    sessions: Mapped[list["ClassSession"]] = relationship(
        secondary=session_instructors,
        back_populates="instructors",
    )