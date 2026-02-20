"""Attendance API routes."""
from datetime import date, datetime
from typing import Annotated

from application.dto.attendance import (
    AttendanceUpdateRequest,
    AttendanceUpdateResponse,
    AttendanceListResponse,
    AttendanceSessionResponse,
    AttendanceStatusResponse,
    ErrorResponse,
)
from domain.entities import SessionStatus
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import get_db
from infrastructure.persistence.repositories.attendance_repository import AttendanceRepository


router = APIRouter()


# Request/Response DTOs (inline for now, should move to application/dto/)
class AttendanceUpdateRequest(BaseModel):
    """Request to mark attendance."""
    status: SessionStatus  # ATTENDED or NO_SHOW
    notes: str | None = None


class AttendanceSessionResponse(BaseModel):
    """Attendance session response."""
    id: int
    booking_id: int
    session_date: datetime
    session_time: str
    status: SessionStatus
    attendance_checked_at: datetime | None = None
    attendance_checked_by: int | None = None
    notes: str | None = None
    student_name: str | None = None
    student_grade: int | None = None

    class Config:
        use_enum_values = True


class AttendanceListResponse(BaseModel):
    """Attendance list response."""
    sessions: list[AttendanceSessionResponse]
    total: int
    offset: int
    limit: int


class AttendanceStatusResponse(BaseModel):
    """Attendance status response."""
    total: int
    by_status: dict[str, int]
    recent_sessions: list[AttendanceSessionResponse]


class ErrorResponse(BaseModel):
    """Error response."""
    code: str
    message: str


def get_attendance_repository(db: AsyncSession = Depends(get_db)) -> AttendanceRepository:
    """Get attendance repository with database session."""
    return AttendanceRepository(db)


@router.patch("/sessions/{session_id}", response_model=AttendanceSessionResponse)
async def mark_attendance(
    session_id: int,
    request: AttendanceUpdateRequest,
    # user_id: int,  # TODO: Get from JWT auth
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Mark attendance for a session.

    Tutors can mark sessions as ATTENDED or NO_SHOW.
    Only sessions with SCHEDULED status can be marked.

    **Validations:**
    - Session must exist
    - Session must be in SCHEDULED status
    - Status must be ATTENDED or NO_SHOW
    """
    # TODO: Get user_id from JWT token
    user_id = 1  # Placeholder

    attendance_repo = get_attendance_repository(db)

    # Validate status
    if request.status not in [SessionStatus.COMPLETED, SessionStatus.NO_SHOW]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_STATUS",
                message="Attendance status must be ATTENDED or NO_SHOW",
            ).model_dump(),
        )

    # Get session
    session = await attendance_repo.get_session_by_id(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="SESSION_NOT_FOUND",
                message="Session not found",
            ).model_dump(),
        )

    # Check if session can be marked
    if session.status != SessionStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="SESSION_ALREADY_MARKED",
                message=f"Session already marked as {session.status.value}",
            ).model_dump(),
        )

    # Update attendance
    updated_session = await attendance_repo.update_session_attendance(
        session_id=session_id,
        status=request.status,
        checked_by=user_id,
    )

    if not updated_session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                code="UPDATE_FAILED",
                message="Failed to update attendance",
            ).model_dump(),
        )

    return AttendanceSessionResponse(
        id=updated_session.id,
        booking_id=updated_session.booking_id,
        session_date=updated_session.session_date,
        session_time=updated_session.session_time,
        status=updated_session.status,
        attendance_checked_at=updated_session.attendance_checked_at,
        attendance_checked_by=updated_session.attendance_checked_by,
        notes=request.notes,
    )


@router.get("/sessions", response_model=AttendanceListResponse)
async def get_sessions_for_attendance(
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date | None = Query(None, description="Filter by date from"),
    date_to: date | None = Query(None, description="Filter by date to"),
    status: str | None = Query(None, description="Filter by status"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    # tutor_id: int,  # TODO: Get from JWT auth
):
    """
    Get sessions that need attendance check.

    Returns sessions for the current tutor with optional filters.
    Only SCHEDULED sessions are returned by default.

    **Filters:**
    - date_from: Only sessions on or after this date
    - date_to: Only sessions on or before this date
    - status: Filter by session status (e.g., "scheduled")
    """
    # TODO: Get tutor_id from JWT token
    tutor_id = 1  # Placeholder

    attendance_repo = get_attendance_repository(db)

    # Convert status string to enum if provided
    status_filter = None
    if status:
        try:
            status_filter = SessionStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    code="INVALID_STATUS",
                    message=f"Invalid status: {status}",
                ).model_dump(),
            )

    sessions_data = await attendance_repo.get_sessions_for_tutor(
        tutor_id=tutor_id,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to,
        offset=offset,
        limit=limit,
    )

    sessions_response = []
    for session_data in sessions_data:
        session = session_data["session"]
        student = session_data["student"]
        sessions_response.append(
            AttendanceSessionResponse(
                id=session.id,
                booking_id=session.booking_id,
                session_date=session.session_date,
                session_time=session.session_time,
                status=session.status,
                attendance_checked_at=session.attendance_checked_at,
                attendance_checked_by=session.attendance_checked_by,
                notes=session.notes,
                student_name=student["name"],
                student_grade=student["grade"],
            )
        )

    return AttendanceListResponse(
        sessions=sessions_response,
        total=len(sessions_response),
        offset=offset,
        limit=limit,
    )


@router.get("/status", response_model=AttendanceStatusResponse)
async def get_attendance_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    offset: int = Query(0, ge=0, description="Pagination offset for recent sessions"),
    limit: int = Query(10, ge=1, le=50, description="Pagination limit for recent sessions"),
    # user_id: int,  # TODO: Get from JWT auth
    # is_tutor: bool,  # TODO: Get from JWT auth
):
    """
    Get attendance status summary for current user.

    Returns:
    - Total session count
    - Count by status (scheduled, completed, cancelled, no_show)
    - Recent sessions with attendance info
    """
    # TODO: Get user_id and is_tutor from JWT token
    user_id = 1
    is_tutor = False  # Set based on user role

    attendance_repo = get_attendance_repository(db)

    status_data = await attendance_repo.get_attendance_status(
        user_id=user_id,
        is_tutor=is_tutor,
        offset=offset,
        limit=limit,
    )

    recent_sessions_response = []
    for session in status_data["recent_sessions"]:
        recent_sessions_response.append(
            AttendanceSessionResponse(
                id=session.id,
                booking_id=session.booking_id,
                session_date=session.session_date,
                session_time=session.session_time,
                status=session.status,
                attendance_checked_at=session.attendance_checked_at,
                attendance_checked_by=session.attendance_checked_by,
                notes=session.notes,
            )
        )

    return AttendanceStatusResponse(
        total=status_data["total"],
        by_status=status_data["by_status"],
        recent_sessions=recent_sessions_response,
    )


@router.get("/health")
async def health_check():
    """Health check endpoint for attendance module."""
    return {"status": "healthy", "module": "attendance"}
