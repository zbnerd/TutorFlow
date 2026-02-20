"""Booking ORM models."""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database import Base


class BookingStatus(str, Enum):
    """Booking status enumeration."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class SessionStatus(str, Enum):
    """Individual session status enumeration."""

    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class Booking(Base):
    """Booking table."""

    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tutor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[BookingStatus] = mapped_column(
        String(20), nullable=False, default=BookingStatus.PENDING
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    sessions: Mapped[list["BookingSession"]] = relationship(
        "BookingSession", back_populates="booking", cascade="all, delete-orphan"
    )


class BookingSession(Base):
    """Individual session within a booking."""

    __tablename__ = "booking_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    session_time: Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM format
    status: Mapped[SessionStatus] = mapped_column(
        String(20), nullable=False, default=SessionStatus.SCHEDULED
    )
    attendance_checked_at: Mapped[datetime | None] = mapped_column(DateTime)
    attendance_checked_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    booking: Mapped["Booking"] = relationship(
        "Booking", back_populates="sessions", single_parent=True
    )

    # Constraints
    __table_args__ = (UniqueConstraint("booking_id", "session_date", "session_time"),)
