"""Attendance DTOs for request/response handling."""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

from domain.entities.attendance import AttendanceStatus
from domain.entities import SessionStatus


class AttendanceMarkRequest(BaseModel):
    """Request to mark attendance for a session."""
    status: AttendanceStatus = Field(..., description="Attendance status (ATTENDED, NO_SHOW, CANCELLED)")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes about the attendance")

    @field_validator("notes")
    @classmethod
    def validate_notes_for_no_show(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that NO_SHOW has required notes if needed."""
        if info.data.get("status") == AttendanceStatus.NO_SHOW and not v:
            # Notes are optional for no-show, but recommended
            pass
        return v


class AttendanceResponse(BaseModel):
    """Attendance record response."""
    id: int
    booking_session_id: int
    status: AttendanceStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttendanceListResponse(BaseModel):
    """Attendance list response for a booking."""
    attendances: List[AttendanceResponse]
    total: int


class NoShowStatsResponse(BaseModel):
    """No-show statistics for a student's bookings with a tutor."""
    tutor_id: int
    student_id: int
    year_month: str  # Format: "2024-01"
    total_sessions: int
    attended_sessions: int
    no_show_count: int
    free_no_show_used: bool  # True if the free no-show (for ONE_FREE policy) has been used


class BatchAttendanceRequest(BaseModel):
    """Request to mark attendance for multiple sessions at once."""
    session_attendances: List["SessionAttendanceItem"] = Field(
        ..., min_items=1, description="List of session attendance records"
    )


class SessionAttendanceItem(BaseModel):
    """Single session attendance item."""
    session_id: int = Field(..., description="Booking session ID")
    status: AttendanceStatus = Field(..., description="Attendance status")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")


class ErrorResponse(BaseModel):
    """Error response."""
    code: str
    message: str
    details: Optional[dict] = None


class AttendanceSessionResponse(BaseModel):
    """Attendance session response."""
    id: int
    booking_id: int
    session_date: datetime
    session_time: str
    status: SessionStatus
    attendance_checked_at: Optional[datetime] = None
    attendance_checked_by: Optional[int] = None
    notes: Optional[str] = None
    student_name: Optional[str] = None
    student_grade: Optional[int] = None

    class Config:
        from_attributes = True
        use_enum_values = True


class AttendanceSessionsListResponse(BaseModel):
    """Attendance sessions list response with pagination."""
    sessions: List[AttendanceSessionResponse]
    total: int
    offset: int
    limit: int


class AttendanceStatusResponse(BaseModel):
    """Attendance status response."""
    total: int
    by_status: dict[str, int]
    recent_sessions: List[AttendanceSessionResponse]
