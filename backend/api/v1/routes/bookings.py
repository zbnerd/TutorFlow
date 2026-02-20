"""Booking API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from application.dto.booking import (
    BookingCreateRequest,
    BookingResponse,
    BookingListResponse,
    BookingApproveRequest,
    BookingRejectRequest,
    ErrorResponse,
)
from application.use_cases.booking import BookingUseCases, BookingValidationError
from domain.value_objects.schedule import ScheduleSlot, TimeRange
from datetime import datetime
from infrastructure.persistence.repositories import BookingRepository
from infrastructure.persistence.repositories.tutor_repository import TutorRepository
from infrastructure.database import get_db


router = APIRouter()


def get_booking_use_cases(db: AsyncSession = Depends(get_db)) -> BookingUseCases:
    """Get booking use cases with dependencies injected."""
    return BookingUseCases(
        booking_repo=BookingRepository(db),
        tutor_repo=TutorRepository(db),
    )


def _parse_schedule_slots(requests: list) -> list[ScheduleSlot]:
    """Parse schedule slot requests to domain objects."""
    slots = []
    for req in requests:
        date = datetime.strptime(req.date, "%Y-%m-%d").date()
        start_time = datetime.strptime(req.start_time, "%H:%M").time()
        end_time = datetime.strptime(req.end_time, "%H:%M").time()

        slots.append(ScheduleSlot(
            date=datetime.combine(date, start_time),
            time_range=TimeRange(start_time, end_time),
        ))
    return slots


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    request: BookingCreateRequest,
    # student_id: int,  # TODO: Get from JWT auth
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new booking request.

    Student creates a booking request for a tutor with requested time slots.
    The booking will be in PENDING status until tutor approval.

    **Validations:**
    - All slots must be at least 24 hours in the future
    - Tutor must be approved
    - No scheduling conflicts with existing bookings
    """
    # TODO: Get student_id from JWT token
    student_id = 1  # Placeholder

    booking_use_cases = get_booking_use_cases(db)

    try:
        slots = _parse_schedule_slots(request.slots)
        booking = await booking_use_cases.create_booking_request(
            student_id=student_id,
            tutor_id=request.tutor_id,
            slots=slots,
            notes=request.notes,
        )
    except BookingValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code=e.code,
                message=e.message,
            ).model_dump(),
        )

    return BookingResponse.model_validate(booking)


@router.get("", response_model=BookingListResponse)
async def list_bookings(
    tutor_id: int | None = Query(None, description="Filter by tutor ID"),
    status: str | None = Query(None, description="Filter by status"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    # user_id: int,  # TODO: Get from JWT auth
    # is_tutor: bool,  # TODO: Get from JWT auth
    db: AsyncSession = Depends(get_db),
):
    """
    List bookings for current user.

    Returns bookings filtered by user role (tutor or student) with optional status filter.
    """
    # TODO: Get user_id and is_tutor from JWT token
    user_id = 1
    is_tutor = False

    booking_use_cases = get_booking_use_cases(db)

    bookings = await booking_use_cases.list_bookings(
        user_id=user_id,
        is_tutor=is_tutor,
        status=status,
        offset=offset,
        limit=limit,
    )

    return BookingListResponse(
        bookings=[BookingResponse.model_validate(b) for b in bookings],
        total=len(bookings),
        offset=offset,
        limit=limit,
    )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get booking details by ID.

    Returns full booking details including sessions.
    """
    booking_use_cases = get_booking_use_cases(db)

    booking = await booking_use_cases.get_booking(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="BOOKING_NOT_FOUND",
                message="Booking not found",
            ).model_dump(),
        )

    return BookingResponse.model_validate(booking)


@router.patch("/{booking_id}/approve", response_model=BookingResponse)
async def approve_booking(
    booking_id: int,
    # tutor_id: int,  # TODO: Get from JWT auth
    db: AsyncSession = Depends(get_db),
):
    """
    Tutor approves a booking request.

    Booking status changes from PENDING to APPROVED.
    """
    # TODO: Get tutor_id from JWT token
    tutor_id = 1

    booking_use_cases = get_booking_use_cases(db)

    try:
        booking = await booking_use_cases.approve_booking(booking_id, tutor_id)
    except BookingValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code=e.code,
                message=e.message,
            ).model_dump(),
        )

    return BookingResponse.model_validate(booking)


@router.patch("/{booking_id}/reject", response_model=BookingResponse)
async def reject_booking(
    booking_id: int,
    request: BookingRejectRequest,
    # tutor_id: int,  # TODO: Get from JWT auth
    db: AsyncSession = Depends(get_db),
):
    """
    Tutor rejects a booking request.

    Booking status changes from PENDING to REJECTED.
    A rejection reason can be provided.
    """
    # TODO: Get tutor_id from JWT token
    tutor_id = 1

    booking_use_cases = get_booking_use_cases(db)

    try:
        booking = await booking_use_cases.reject_booking(
            booking_id,
            tutor_id,
            request.reason,
        )
    except BookingValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code=e.code,
                message=e.message,
            ).model_dump(),
        )

    return BookingResponse.model_validate(booking)


@router.delete("/{booking_id}", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    # user_id: int,  # TODO: Get from JWT auth
    # is_tutor: bool,  # TODO: Get from JWT auth
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a booking.

    Both students and tutors can cancel bookings.
    Only PENDING and APPROVED bookings can be cancelled.
    """
    # TODO: Get user_id and is_tutor from JWT token
    user_id = 1
    is_tutor = False

    booking_use_cases = get_booking_use_cases(db)

    try:
        booking = await booking_use_cases.cancel_booking(
            booking_id,
            user_id,
            is_tutor,
        )
    except BookingValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code=e.code,
                message=e.message,
            ).model_dump(),
        )

    return BookingResponse.model_validate(booking)
