"""Attendance API routes."""
from datetime import date, datetime
from typing import Annotated

from application.dto.attendance import (
    AttendanceSessionResponse,
    AttendanceStatusResponse,
    AttendanceMarkRequest,
    AttendanceSessionsListResponse,
)
from application.dto import ErrorResponse
from api.v1.routes.dependencies import (
    get_current_user,
    get_current_tutor_or_admin,
    get_repository_factory,
)
from domain.entities import SessionStatus, User
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import get_db
from infrastructure.persistence.repository_factory import RepositoryFactory


router = APIRouter()


# Alias for backward compatibility
AttendanceListResponse = AttendanceSessionsListResponse


@router.patch("/sessions/{session_id}", response_model=AttendanceSessionResponse)
async def mark_attendance(
    session_id: int,
    request: AttendanceMarkRequest,
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
    current_user: Annotated[User, Depends(get_current_user)],
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
    user_id = current_user.id

    attendance_repo = repos.attendance()

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
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
    date_from: date | None = Query(None, description="Filter by date from"),
    date_to: date | None = Query(None, description="Filter by date to"),
    status: str | None = Query(None, description="Filter by status"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
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
    # For tutors, get their own sessions. For students, get their booking sessions
    from domain.entities import UserRole
    tutor_id = current_user.id if current_user.role == UserRole.TUTOR else None

    attendance_repo = repos.attendance()

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
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
    offset: int = Query(0, ge=0, description="Pagination offset for recent sessions"),
    limit: int = Query(10, ge=1, le=50, description="Pagination limit for recent sessions"),
):
    """
    Get attendance status summary for current user.

    Returns:
    - Total session count
    - Count by status (scheduled, completed, cancelled, no_show)
    - Recent sessions with attendance info
    """
    user_id = current_user.id
    from domain.entities import UserRole
    is_tutor = current_user.role == UserRole.TUTOR

    attendance_repo = repos.attendance()

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
