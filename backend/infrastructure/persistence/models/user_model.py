"""User, Tutor, Student ORM models."""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    ARRAY,
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


class UserRole(str, Enum):
    """User role enumeration."""

    TUTOR = "TUTOR"
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"


class NoShowPolicy(str, Enum):
    """No-show policy enumeration."""

    FULL_DEDUCTION = "FULL_DEDUCTION"
    ONE_FREE = "ONE_FREE"
    NONE = "NONE"


class User(Base):
    """User table (unified for tutors, students, admins)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    kakao_id: Mapped[int] = mapped_column(unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    profile_url: Mapped[str | None] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(20))
    role: Mapped[UserRole] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    tutor: Mapped["Tutor"] = relationship(
        "Tutor", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    student: Mapped["Student"] = relationship(
        "Student", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class Tutor(Base):
    """Tutor extended information."""

    __tablename__ = "tutors"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    bio: Mapped[str | None] = mapped_column(Text)
    subjects: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    region: Mapped[str | None] = mapped_column(String(100))
    hourly_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    no_show_policy: Mapped[NoShowPolicy] = mapped_column(
        String(20), nullable=False, default=NoShowPolicy.FULL_DEDUCTION
    )
    cancellation_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    bank_name: Mapped[str | None] = mapped_column(String(50))
    bank_account: Mapped[str | None] = mapped_column(String(50))
    bank_holder: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="tutor", single_parent=True
    )
    available_slots: Mapped[list["AvailableSlot"]] = relationship(
        "AvailableSlot", back_populates="tutor", cascade="all, delete-orphan"
    )


class Student(Base):
    """Student extended information."""

    __tablename__ = "students"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    grade: Mapped[int | None] = mapped_column(Integer)
    parent_name: Mapped[str | None] = mapped_column(String(50))
    parent_phone: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="student", single_parent=True
    )


class AvailableSlot(Base):
    """Tutor available time slots."""

    __tablename__ = "available_slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tutor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tutors.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0(월) ~ 6(일)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM format
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM format
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    tutor: Mapped["Tutor"] = relationship(
        "Tutor", back_populates="available_slots", single_parent=True
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("tutor_id", "day_of_week", "start_time", "end_time"),
    )
