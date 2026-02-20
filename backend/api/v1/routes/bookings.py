"""Booking API routes."""
from typing import Annotated

from api.v1.routes.dependencies import get_current_user, get_current_student, get_current_tutor, get_repository_factory
from application.dto.booking import (
    BookingCreateRequest,
    BookingResponse,
    BookingListResponse,
    BookingApproveRequest,
    BookingRejectRequest,
    ErrorResponse,
)
from application.use_cases.booking import BookingUseCases, BookingValidationError
from domain.entities import User, UserRole
from domain.value_objects.schedule import ScheduleSlot, TimeRange
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.persistence.repository_factory import RepositoryFactory


router = APIRouter()


def get_booking_use_cases(repos: RepositoryFactory) -> BookingUseCases:
    """Get booking use cases with dependencies injected."""
    return BookingUseCases(
        booking_repo=repos.booking(),
        tutor_repo=repos.tutor(),
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
    current_user: Annotated[User, Depends(get_current_student)],
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
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
    student_id = current_user.id

    booking_use_cases = get_booking_use_cases(repos)

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
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
    tutor_id: int | None = Query(None, description="Filter by tutor ID"),
    status: str | None = Query(None, description="Filter by status"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
):
    """
    List bookings for current user.

    Returns bookings filtered by user role (tutor or student) with optional status filter.
    """
    user_id = current_user.id
    is_tutor = current_user.role == UserRole.TUTOR

    booking_use_cases = get_booking_use_cases(repos)

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
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
):
    """
    Get booking details by ID.

    Returns full booking details including sessions.
    """
    booking_use_cases = get_booking_use_cases(repos)

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
    current_user: Annotated[User, Depends(get_current_tutor)],
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
):
    """
    Tutor approves a booking request.

    Booking status changes from PENDING to APPROVED.
    """
    tutor_id = current_user.id

    booking_use_cases = get_booking_use_cases(repos)

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
    current_user: Annotated[User, Depends(get_current_tutor)],
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
):
    """
    Tutor rejects a booking request.

    Booking status changes from PENDING to REJECTED.
    A rejection reason can be provided.
    """
    tutor_id = current_user.id

    booking_use_cases = get_booking_use_cases(repos)

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
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
):
    """
    Cancel a booking.

    Both students and tutors can cancel bookings.
    Only PENDING and APPROVED bookings can be cancelled.
    """
    user_id = current_user.id
    is_tutor = current_user.role == UserRole.TUTOR

    booking_use_cases = get_booking_use_cases(repos)

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
