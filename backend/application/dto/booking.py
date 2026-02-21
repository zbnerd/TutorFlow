"""Booking DTOs for request/response handling."""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

from domain.entities import BookingStatus


class ScheduleSlotRequest(BaseModel):
    """Schedule slot request."""
    date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Validate date format."""
        from datetime import datetime
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        """Validate time format."""
        from datetime import datetime
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("Time must be in HH:MM format")
        return v


class BookingCreateRequest(BaseModel):
    """Booking creation request."""
    tutor_id: int = Field(..., description="Tutor ID")
    slots: List[ScheduleSlotRequest] = Field(
        ..., min_items=1, description="Requested schedule slots"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes from student")


class BookingResponse(BaseModel):
    """Booking response."""
    id: int
    student_id: int
    tutor_id: int
    total_sessions: int
    completed_sessions: int
    status: BookingStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    """Booking list response."""
    bookings: List[BookingResponse]
    total: int
    offset: int
    limit: int


class BookingApproveRequest(BaseModel):
    """Booking approve request (empty body, just authorization needed)."""
    pass


class BookingRejectRequest(BaseModel):
    """Booking reject request."""
    reason: Optional[str] = Field(None, max_length=500, description="Rejection reason")
