"""SQLAlchemy ORM models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Numeric,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database import Base
from domain.entities import UserRole, BookingStatus, PaymentStatus, SessionStatus, NoShowPolicy


class UserModel(Base):
    """User ORM model."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    oauth_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    profile_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tutor: Mapped[Optional["TutorModel"]] = relationship("TutorModel", back_populates="user", uselist=False)
    student: Mapped[Optional["StudentModel"]] = relationship("StudentModel", back_populates="user", uselist=False)

    def to_entity(self):
        """Convert ORM model to domain entity."""
        from domain.entities import User

        return User(
            id=self.id,
            email=self.email,
            name=self.name,
            phone=self.phone,
            role=self.role,
            oauth_provider=self.oauth_provider,
            oauth_id=self.oauth_id,
            profile_image_url=self.profile_image_url,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, user):
        """Create ORM model from domain entity."""
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            phone=user.phone,
            role=user.role,
            oauth_provider=user.oauth_provider,
            oauth_id=user.oauth_id,
            profile_image_url=user.profile_image_url,
            is_active=user.is_active,
        )


class TutorModel(Base):
    """Tutor profile ORM model."""
    __tablename__ = "tutors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subjects: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # ["수학", "영어"]
    hourly_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # KRW
    no_show_policy: Mapped[NoShowPolicy] = mapped_column(Enum(NoShowPolicy), default=NoShowPolicy.FULL_DEDUCTION)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    bank_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bank_account: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_holder: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="tutor")


class StudentModel(Base):
    """Student profile ORM model."""
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    grade: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-12
    parent_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    parent_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="student")


class AvailableSlotModel(Base):
    """Tutor available time slot ORM model."""
    __tablename__ = "available_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tutor_id: Mapped[int] = mapped_column(ForeignKey("tutors.id"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "14:00"
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "18:00"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class BookingModel(Base):
    """Booking ORM model."""
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    tutor_id: Mapped[int] = mapped_column(ForeignKey("tutors.id"), nullable=False)
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_sessions: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.PENDING)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BookingSessionModel(Base):
    """Individual session ORM model."""
    __tablename__ = "booking_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    session_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    session_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "14:00"
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.SCHEDULED)
    attendance_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    attendance_checked_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PaymentModel(Base):
    """Payment ORM model."""
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # KRW
    fee_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.05)  # 5%
    fee_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # KRW
    net_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # KRW
    pg_payment_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pg_provider: Mapped[str] = mapped_column(String(50), default="toss")
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    refund_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SettlementModel(Base):
    """Monthly settlement ORM model."""
    __tablename__ = "settlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tutor_id: Mapped[int] = mapped_column(ForeignKey("tutors.id"), nullable=False)
    year_month: Mapped[str] = mapped_column(String(7), nullable=False)  # "2024-01"
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # KRW
    total_fee: Mapped[int] = mapped_column(Integer, nullable=False)  # KRW
    net_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # KRW
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReviewModel(Base):
    """Review ORM model."""
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False, unique=True)
    tutor_id: Mapped[int] = mapped_column(ForeignKey("tutors.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    overall_rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    kindness_rating: Mapped[int] = mapped_column(Integer, default=5)
    preparation_rating: Mapped[int] = mapped_column(Integer, default=5)
    improvement_rating: Mapped[int] = mapped_column(Integer, default=5)
    punctuality_rating: Mapped[int] = mapped_column(Integer, default=5)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    tutor_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tutor_replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_entity(self):
        """Convert ORM model to domain entity."""
        from domain.entities import Review

        return Review(
            id=self.id,
            booking_id=self.booking_id,
            tutor_id=self.tutor_id,
            student_id=self.student_id,
            overall_rating=self.overall_rating,
            kindness_rating=self.kindness_rating,
            preparation_rating=self.preparation_rating,
            improvement_rating=self.improvement_rating,
            punctuality_rating=self.punctuality_rating,
            content=self.content,
            is_anonymous=self.is_anonymous,
            tutor_reply=self.tutor_reply,
            tutor_replied_at=self.tutor_replied_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class ReviewReportModel(Base):
    """Review report ORM model."""
    __tablename__ = "review_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), nullable=False)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reason: Mapped[str] = mapped_column(String(50), nullable=False)  # spam, abuse, false_info
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_entity(self):
        """Convert ORM model to domain entity."""
        from domain.entities import ReviewReport

        return ReviewReport(
            id=self.id,
            review_id=self.review_id,
            reporter_id=self.reporter_id,
            reason=self.reason,
            description=self.description,
            is_processed=self.is_processed,
            processed_by=self.processed_by,
            processed_at=self.processed_at,
            created_at=self.created_at,
        )


class AuditLogModel(Base):
    """Audit log ORM model."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actor_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
