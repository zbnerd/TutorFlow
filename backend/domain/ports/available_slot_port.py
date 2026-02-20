"""AvailableSlot repository port for managing tutor availability slots."""
from typing import Protocol, runtime_checkable, List, Optional

from domain.entities import AvailableSlot


@runtime_checkable
class AvailableSlotRepositoryPort(Protocol):
    """AvailableSlot repository interface."""

    async def get_tutor_slots(
        self,
        tutor_id: int,
        active_only: bool = True,
    ) -> List[AvailableSlot]:
        """Get all available slots for a tutor.

        Args:
            tutor_id: Tutor ID
            active_only: If True, only return active slots

        Returns:
            List of available slots
        """

    async def create_slot(
        self,
        tutor_id: int,
        day_of_week: int,
        start_time: str,
        end_time: str,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> AvailableSlot:
        """Create a new available slot.

        Args:
            tutor_id: Tutor ID
            day_of_week: Day of week (0=Monday, 6=Sunday)
            start_time: Start time in "HH:MM" format
            end_time: End time in "HH:MM" format
            actor_id: ID of user creating the slot
            ip_address: IP address of the request

        Returns:
            Created slot
        """

    async def update_slot(
        self,
        slot_id: int,
        day_of_week: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        is_active: Optional[bool] = None,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[AvailableSlot]:
        """Update an available slot.

        Args:
            slot_id: Slot ID
            day_of_week: New day of week
            start_time: New start time
            end_time: New end time
            is_active: New active status
            actor_id: ID of user updating the slot
            ip_address: IP address of the request

        Returns:
            Updated slot if found, None otherwise
        """

    async def delete_slot(
        self,
        slot_id: int,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> bool:
        """Delete an available slot.

        Args:
            slot_id: Slot ID
            actor_id: ID of user deleting the slot
            ip_address: IP address of the request

        Returns:
            True if deleted, False if not found
        """

    async def check_availability(
        self,
        tutor_id: int,
        day_of_week: int,
        time: str,
    ) -> bool:
        """Check if tutor is available at a specific time.

        Args:
            tutor_id: Tutor ID
            day_of_week: Day of week (0=Monday, 6=Sunday)
            time: Time in "HH:MM" format

        Returns:
            True if tutor has an active slot covering this time
        """

    async def get_slot_by_id(self, slot_id: int) -> Optional[AvailableSlot]:
        """Get a slot by ID.

        Args:
            slot_id: Slot ID

        Returns:
            Slot if found, None otherwise
        """
