"""Port interfaces for external dependencies (Protocol definitions)."""

from typing import Protocol, runtime_checkable, List, Optional
from datetime import datetime

from domain.entities import User, Tutor, Student, Booking, BookingSession, Payment, Review
from domain.value_objects.schedule import ScheduleSlot


@runtime_checkable
class BookingRepositoryPort(Protocol):
    """Booking repository interface."""

    async def save(self, booking: Booking) -> Booking:
        """Save booking to database."""

    async def find_by_id(self, booking_id: int) -> Optional[Booking]:
        """Find booking by ID."""

    async def list_by_tutor(
        self,
        tutor_id: int,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Booking]:
        """List bookings by tutor."""

    async def list_by_student(
        self,
        student_id: int,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Booking]:
        """List bookings by student."""

    async def find_conflicting_slots(
        self,
        tutor_id: int,
        slots: List[ScheduleSlot],
    ) -> List[ScheduleSlot]:
        """Find existing bookings that conflict with given slots."""

    async def create_sessions(
        self,
        booking_id: int,
        slots: List[ScheduleSlot],
    ) -> List[BookingSession]:
        """Create booking sessions from schedule slots."""


# Keep existing ports...
