"""Domain entities representing core business objects."""
from datetime import datetime
from enum import Enum
from typing import Literal
from dataclasses import dataclass


class UserRole(str, Enum):
    """User role types."""
    TUTOR = "tutor"
    STUDENT = "student"
    ADMIN = "admin"


class BookingStatus(str, Enum):
    """Booking status types."""
    PENDING = "pending"  # Initial state, waiting tutor approval
    APPROVED = "approved"  # Tutor approved, sessions scheduled
    IN_PROGRESS = "in_progress"  # Sessions ongoing
    COMPLETED = "completed"  # All sessions done
    CANCELLED = "cancelled"  # Booking cancelled
    REJECTED = "rejected"  # Tutor rejected


class PaymentStatus(str, Enum):
    """Payment status types."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class SessionStatus(str, Enum):
    """Individual session status."""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class NoShowPolicy(str, Enum):
    """Tutor's no-show policy."""
    FULL_DEDUCTION = "full_deduction"  # Absence counts as paid session
    ONE_FREE = "one_free"  # One free absence per month
    NONE = "none"  # Manual handling


@dataclass
class Money:
    """Value object for monetary amounts."""
    amount_krw: int

    def __post_init__(self):
        if self.amount_krw < 0:
            raise ValueError("Amount cannot be negative")

    def add(self, other: "Money") -> "Money":
        return Money(self.amount_krw + other.amount_krw)

    def subtract(self, other: "Money") -> "Money":
        return Money(self.amount_krw - other.amount_krw)

    def calculate_fee(self, fee_rate: float) -> "Money":
        """Calculate platform fee."""
        return Money(int(self.amount_krw * fee_rate))

    def __str__(self) -> str:
        return f"{self.amount_krw:,}원"


@dataclass
class User:
    """User entity (tutors, students, admins)."""
    id: int | None = None
    email: str | None = None
    name: str | None = None
    phone: str | None = None
    role: UserRole | None = None
    oauth_provider: str | None = None  # "kakao"
    oauth_id: str | None = None
    profile_image_url: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Tutor:
    """Tutor profile entity."""
    id: int | None = None
    user_id: int | None = None
    bio: str | None = None
    subjects: list[str] | None = None  # ["수학", "영어"]
    hourly_rate: Money | None = None
    no_show_policy: NoShowPolicy = NoShowPolicy.FULL_DEDUCTION
    is_approved: bool = False  # Admin approval required
    bank_name: str | None = None
    bank_account: str | None = None
    bank_holder: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Student:
    """Student profile entity."""
    id: int | None = None
    user_id: int | None = None
    grade: int | None = None  # 1-12 for K-12
    parent_name: str | None = None
    parent_phone: str | None = None
    address: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class AvailableSlot:
    """Tutor's available time slot."""
    id: int | None = None
    tutor_id: int | None = None
    day_of_week: int | None = None  # 0=Monday, 6=Sunday
    start_time: str | None = None  # "14:00"
    end_time: str | None = None  # "18:00"
    is_active: bool = True


@dataclass
class Booking:
    """Booking entity."""
    id: int | None = None
    student_id: int | None = None
    tutor_id: int | None = None
    total_sessions: int | None = None
    completed_sessions: int = 0
    status: BookingStatus = BookingStatus.PENDING
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class BookingSession:
    """Individual session within a booking."""
    id: int | None = None
    booking_id: int | None = None
    session_date: datetime | None = None
    session_time: str | None = None  # "14:00"
    status: SessionStatus = SessionStatus.SCHEDULED
    attendance_checked_at: datetime | None = None
    attendance_checked_by: int | None = None  # user_id
    notes: str | None = None


@dataclass
class Payment:
    """Payment entity."""
    id: int | None = None
    booking_id: int | None = None
    amount: Money | None = None
    fee_rate: float = 0.05  # 5% platform fee
    fee_amount: Money | None = None
    net_amount: Money | None = None  # amount - fee_amount
    pg_payment_key: str | None = None  # Toss Payments payment key
    pg_provider: str = "toss"
    status: PaymentStatus = PaymentStatus.PENDING
    paid_at: datetime | None = None
    refunded_at: datetime | None = None
    refund_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        if self.amount and self.fee_amount is None:
            self.fee_amount = self.amount.calculate_fee(self.fee_rate)
        if self.amount and self.fee_amount and self.net_amount is None:
            self.net_amount = self.amount.subtract(self.fee_amount)


# Import settlement entities
from domain.entities.settlement import Settlement, SettlementStatus


@dataclass
class Review:
    """Review entity (verified-payment only)."""
    id: int | None = None
    booking_id: int | None = None
    tutor_id: int | None = None
    student_id: int | None = None
    overall_rating: int | None = None  # 1-5
    kindness_rating: int = 5
    preparation_rating: int = 5
    improvement_rating: int = 5
    punctuality_rating: int = 5
    content: str | None = None
    is_anonymous: bool = True
    tutor_reply: str | None = None
    tutor_replied_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        # Validate rating range
        for rating in [
            self.overall_rating, self.kindness_rating,
            self.preparation_rating, self.improvement_rating,
            self.punctuality_rating
        ]:
            if rating is not None and not 1 <= rating <= 5:
                raise ValueError("Ratings must be between 1 and 5")


@dataclass
class ReviewReport:
    """Review report for moderation."""
    id: int | None = None
    review_id: int | None = None
    reporter_id: int | None = None
    reason: str | None = None  # spam, abuse, false_info
    description: str | None = None
    is_processed: bool = False
    processed_by: int | None = None
    processed_at: datetime | None = None
    created_at: datetime | None = None


@dataclass
class AuditLog:
    """Audit log for all state changes."""
    id: int | None = None
    entity_type: str | None = None  # "booking", "payment", "review"
    entity_id: int | None = None
    action: str | None = None  # "create", "update", "delete"
    old_value: str | None = None
    new_value: str | None = None
    actor_id: int | None = None
    ip_address: str | None = None
    created_at: datetime | None = None


# Import attendance entities
from domain.entities.attendance import (
    Attendance,
    AttendanceStatus,
    NoShowPolicyType,
    FULL_DEDUCTION,
    ONE_FREE,
    NONE,
)

# Import badge entities
from domain.entities.badge import (
    Badge,
    POPULAR_TUTOR,
    BEST_TUTOR,
    RESPONSE_KING,
    ALL_BADGES,
    BADGE_MAP,
)

__all__ = [
    "UserRole",
    "BookingStatus",
    "PaymentStatus",
    "SessionStatus",
    "NoShowPolicy",
    "Money",
    "User",
    "Tutor",
    "Student",
    "AvailableSlot",
    "Booking",
    "BookingSession",
    "Payment",
    "Settlement",
    "SettlementStatus",
    "Review",
    "ReviewReport",
    "AuditLog",
    "Attendance",
    "AttendanceStatus",
    "NoShowPolicyType",
    "FULL_DEDUCTION",
    "ONE_FREE",
    "NONE",
    "Badge",
    "POPULAR_TUTOR",
    "BEST_TUTOR",
    "RESPONSE_KING",
    "ALL_BADGES",
    "BADGE_MAP",
]
