"""Port interfaces for external dependencies (Protocol definitions)."""

from typing import Protocol, runtime_checkable, List, Optional
from datetime import datetime

from domain.entities import User, Tutor, Student, Booking, BookingSession, Payment, Review, Settlement, Money
from domain.value_objects.schedule import ScheduleSlot
from domain.ports.audit_port import AuditPort
from domain.ports.available_slot_port import AvailableSlotRepositoryPort


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


@runtime_checkable
class SettlementRepositoryPort(Protocol):
    """Settlement repository interface."""

    async def save(self, settlement: Settlement) -> Settlement:
        """Save settlement to database."""

    async def find_by_id(self, settlement_id: int) -> Optional[Settlement]:
        """Find settlement by ID."""

    async def get_monthly_settlements(
        self,
        tutor_id: int,
        year_month: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Settlement]:
        """Get monthly settlements for a tutor."""

    async def find_by_tutor_and_month(
        self,
        tutor_id: int,
        year_month: str,
    ) -> Optional[Settlement]:
        """Find settlement by tutor and year_month."""

    async def create_settlement(
        self,
        tutor_id: int,
        year_month: str,
        total_sessions: int,
        total_amount: Money,
        platform_fee: Money,
        pg_fee: Money,
    ) -> Settlement:
        """Create a new settlement record."""

    async def mark_as_paid(
        self,
        settlement_id: int,
        paid_at: Optional[datetime] = None,
    ) -> Settlement:
        """Mark settlement as paid."""

    async def list_pending_settlements(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Settlement]:
        """List all pending settlements (not yet paid)."""


# Keep existing ports...
