"""Data Transfer Objects."""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from domain.entities import UserRole, NoShowPolicy, BookingStatus, PaymentStatus


class UserResponse(BaseModel):
    """User response DTO."""
    id: int
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole
    profile_image_url: Optional[str] = None

    class Config:
        from_attributes = True


class TutorCreate(BaseModel):
    """Tutor profile creation DTO."""
    bio: Optional[str] = None
    subjects: list[str] = []
    hourly_rate: int = Field(gt=0, description="Hourly rate in KRW")
    no_show_policy: NoShowPolicy = NoShowPolicy.FULL_DEDUCTION
    bank_name: str
    bank_account: str
    bank_holder: str


class TutorResponse(BaseModel):
    """Tutor profile response DTO."""
    id: int
    user_id: int
    bio: Optional[str] = None
    subjects: list[str] = []
    hourly_rate: int
    no_show_policy: NoShowPolicy
    is_approved: bool

    class Config:
        from_attributes = True


class StudentCreate(BaseModel):
    """Student profile creation DTO."""
    grade: int = Field(ge=1, le=12, description="Grade level 1-12")
    parent_name: str
    parent_phone: str
    address: Optional[str] = None


class BookingCreate(BaseModel):
    """Booking creation DTO."""
    tutor_id: int
    total_sessions: int = Field(gt=0, description="Number of sessions")
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    """Booking response DTO."""
    id: int
    student_id: int
    tutor_id: int
    total_sessions: int
    completed_sessions: int
    status: BookingStatus
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    """Payment response DTO."""
    id: int
    booking_id: int
    amount: int
    fee_rate: float
    fee_amount: int
    net_amount: int
    status: PaymentStatus

    class Config:
        from_attributes = True


# Import attendance DTOs
from application.dto.attendance import (
    AttendanceMarkRequest,
    AttendanceResponse,
    AttendanceListResponse,
    NoShowStatsResponse,
    BatchAttendanceRequest,
    SessionAttendanceItem,
)

__all__ = [
    "UserResponse",
    "TutorCreate",
    "TutorResponse",
    "StudentCreate",
    "BookingCreate",
    "BookingResponse",
    "PaymentResponse",
    "AttendanceMarkRequest",
    "AttendanceResponse",
    "AttendanceListResponse",
    "NoShowStatsResponse",
    "BatchAttendanceRequest",
    "SessionAttendanceItem",
]
