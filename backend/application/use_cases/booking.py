"""Booking use cases for managing tutoring bookings."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from domain.entities import Booking, BookingStatus, Tutor
from domain.ports import BookingRepositoryPort, TutorRepositoryPort
from domain.value_objects.schedule import ScheduleSlot, find_schedule_conflicts


class BookingValidationError(Exception):
    """Raised when booking validation fails."""

    def __init__(self, message: str, code: str = "BOOKING_VALIDATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


@dataclass
class BookingUseCases:
    """Booking management use cases."""

    booking_repo: BookingRepositoryPort
    tutor_repo: TutorRepositoryPort

    async def create_booking_request(
        self,
        student_id: int,
        tutor_id: int,
        slots: List[ScheduleSlot],
        notes: Optional[str] = None,
    ) -> Booking:
        """
        Create a new booking request from student.

        Validations:
        - All slots must be at least 24 hours in the future
        - Tutor must be approved
        - No scheduling conflicts with existing bookings

        Args:
            student_id: Student's ID
            tutor_id: Tutor's ID
            slots: List of requested schedule slots
            notes: Optional notes from student

        Returns:
            Created booking entity

        Raises:
            BookingValidationError: If validation fails
        """
        # Validate tutor exists and is approved
        tutor = await self.tutor_repo.find_by_id(tutor_id)
        if not tutor:
            raise BookingValidationError("Tutor not found", "TUTOR_NOT_FOUND")

        if not tutor.is_approved:
            raise BookingValidationError("Tutor is not approved", "TUTOR_NOT_APPROVED")

        # Validate all slots are in the future (minimum 24 hours)
        for slot in slots:
            if not slot.is_future():
                raise BookingValidationError(
                    (
                        f"Slot {slot.date} {slot.time_range.start_time} "
                        f"is not at least 24 hours in the future"
                    ),
                    "SLOT_TOO_SOON",
                )

        # Check for scheduling conflicts
        conflicts = await self.booking_repo.find_conflicting_slots(tutor_id, slots)
        if conflicts:
            conflict_list = ", ".join(
                f"{s.date} {s.time_range.start_time}" for s in conflicts
            )
            raise BookingValidationError(
                f"Scheduling conflicts at: {conflict_list}",
                "SCHEDULE_CONFLICT",
            )

        # Create booking
        booking = Booking(
            student_id=student_id,
            tutor_id=tutor_id,
            total_sessions=len(slots),
            completed_sessions=0,
            status=BookingStatus.PENDING,
            notes=notes,
        )

        booking = await self.booking_repo.save(booking)

        # Create booking sessions
        await self.booking_repo.create_sessions(booking.id, slots)

        return booking

    async def approve_booking(self, booking_id: int, tutor_id: int) -> Booking:
        """
        Tutor approves a booking request.

        Args:
            booking_id: Booking ID to approve
            tutor_id: Tutor ID (for authorization)

        Returns:
            Updated booking entity

        Raises:
            BookingValidationError: If booking not found or not authorized
        """
        booking = await self.booking_repo.find_by_id(booking_id)
        if not booking:
            raise BookingValidationError("Booking not found", "BOOKING_NOT_FOUND")

        if booking.tutor_id != tutor_id:
            raise BookingValidationError("Not authorized to approve this booking", "NOT_AUTHORIZED")

        if booking.status != BookingStatus.PENDING:
            raise BookingValidationError(
                f"Cannot approve booking with status {booking.status.value}",
                "INVALID_STATUS",
            )

        booking.status = BookingStatus.APPROVED
        return await self.booking_repo.save(booking)

    async def reject_booking(
        self,
        booking_id: int,
        tutor_id: int,
        reason: Optional[str] = None,
    ) -> Booking:
        """
        Tutor rejects a booking request.

        Args:
            booking_id: Booking ID to reject
            tutor_id: Tutor ID (for authorization)
            reason: Optional rejection reason

        Returns:
            Updated booking entity

        Raises:
            BookingValidationError: If booking not found or not authorized
        """
        booking = await self.booking_repo.find_by_id(booking_id)
        if not booking:
            raise BookingValidationError("Booking not found", "BOOKING_NOT_FOUND")

        if booking.tutor_id != tutor_id:
            raise BookingValidationError("Not authorized to reject this booking", "NOT_AUTHORIZED")

        if booking.status != BookingStatus.PENDING:
            raise BookingValidationError(
                f"Cannot reject booking with status {booking.status.value}",
                "INVALID_STATUS",
            )

        booking.status = BookingStatus.REJECTED
        booking.notes = f"[REJECTED] {reason or 'No reason provided'}\n{booking.notes or ''}"
        return await self.booking_repo.save(booking)

    async def cancel_booking(
        self,
        booking_id: int,
        user_id: int,
        is_tutor: bool = False,
    ) -> Booking:
        """
        Cancel a booking (by student or tutor).

        Args:
            booking_id: Booking ID to cancel
            user_id: User ID (student or tutor)
            is_tutor: True if user is tutor, False if student

        Returns:
            Updated booking entity

        Raises:
            BookingValidationError: If booking not found or not authorized
        """
        booking = await self.booking_repo.find_by_id(booking_id)
        if not booking:
            raise BookingValidationError("Booking not found", "BOOKING_NOT_FOUND")

        # Check authorization
        if is_tutor:
            if booking.tutor_id != user_id:
                raise BookingValidationError(
                    "Not authorized to cancel this booking", "NOT_AUTHORIZED"
                )
        else:
            if booking.student_id != user_id:
                raise BookingValidationError(
                    "Not authorized to cancel this booking", "NOT_AUTHORIZED"
                )

        # Can only cancel pending or approved bookings
        if booking.status not in [BookingStatus.PENDING, BookingStatus.APPROVED]:
            raise BookingValidationError(
                f"Cannot cancel booking with status {booking.status.value}",
                "INVALID_STATUS",
            )

        booking.status = BookingStatus.CANCELLED
        return await self.booking_repo.save(booking)

    async def list_bookings(
        self,
        user_id: int,
        is_tutor: bool,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Booking]:
        """
        List bookings for a tutor or student.

        Args:
            user_id: User ID
            is_tutor: True if user is tutor, False if student
            status: Optional status filter
            offset: Pagination offset
            limit: Pagination limit

        Returns:
            List of booking entities
        """
        if is_tutor:
            return await self.booking_repo.list_by_tutor(user_id, status, offset, limit)
        else:
            return await self.booking_repo.list_by_student(user_id, status, offset, limit)

    async def get_booking(self, booking_id: int) -> Optional[Booking]:
        """
        Get booking by ID.

        Args:
            booking_id: Booking ID

        Returns:
            Booking entity or None
        """
        return await self.booking_repo.find_by_id(booking_id)
