"""AvailableSlot use cases for managing tutor availability."""
from dataclasses import dataclass
from typing import List, Optional

from domain.entities import AvailableSlot
from domain.ports import AvailableSlotRepositoryPort, TutorRepositoryPort


class SlotValidationError(Exception):
    """Raised when slot validation fails."""

    def __init__(self, message: str, code: str = "SLOT_VALIDATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


@dataclass
class AvailableSlotUseCases:
    """Available slot management use cases."""

    slot_repo: AvailableSlotRepositoryPort
    tutor_repo: TutorRepositoryPort

    async def create_slot(
        self,
        tutor_id: int,
        day_of_week: int,
        start_time: str,
        end_time: str,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> AvailableSlot:
        """
        Create a new available slot for a tutor.

        Validations:
        - Tutor must exist
        - day_of_week must be 0-6 (Monday-Sunday)
        - start_time must be before end_time
        - Time format must be "HH:MM"

        Args:
            tutor_id: Tutor's ID
            day_of_week: Day of week (0=Monday, 6=Sunday)
            start_time: Start time in "HH:MM" format
            end_time: End time in "HH:MM" format
            actor_id: ID of user creating the slot
            ip_address: IP address of the request

        Returns:
            Created slot entity

        Raises:
            SlotValidationError: If validation fails
        """
        # Validate tutor exists
        tutor = await self.tutor_repo.find_by_id(tutor_id)
        if not tutor:
            raise SlotValidationError("Tutor not found", "TUTOR_NOT_FOUND")

        # Validate day_of_week range
        if not 0 <= day_of_week <= 6:
            raise SlotValidationError(
                "day_of_week must be between 0 (Monday) and 6 (Sunday)",
                "INVALID_DAY_OF_WEEK",
            )

        # Validate time format
        try:
            start_hour, start_minute = map(int, start_time.split(":"))
            end_hour, end_minute = map(int, end_time.split(":"))
        except ValueError:
            raise SlotValidationError(
                "Time must be in 'HH:MM' format",
                "INVALID_TIME_FORMAT",
            )

        # Validate time values
        if not (0 <= start_hour <= 23 and 0 <= start_minute <= 59):
            raise SlotValidationError("Invalid start time", "INVALID_START_TIME")
        if not (0 <= end_hour <= 23 and 0 <= end_minute <= 59):
            raise SlotValidationError("Invalid end time", "INVALID_END_TIME")

        # Validate start_time is before end_time
        if start_time >= end_time:
            raise SlotValidationError(
                "start_time must be before end_time",
                "INVALID_TIME_RANGE",
            )

        # Create the slot
        return await self.slot_repo.create_slot(
            tutor_id=tutor_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            actor_id=actor_id,
            ip_address=ip_address,
        )

    async def get_tutor_slots(
        self,
        tutor_id: int,
        active_only: bool = True,
    ) -> List[AvailableSlot]:
        """
        Get all available slots for a tutor.

        Args:
            tutor_id: Tutor's ID
            active_only: If True, only return active slots

        Returns:
            List of available slots
        """
        # Validate tutor exists
        tutor = await self.tutor_repo.find_by_id(tutor_id)
        if not tutor:
            raise SlotValidationError("Tutor not found", "TUTOR_NOT_FOUND")

        return await self.slot_repo.get_tutor_slots(tutor_id, active_only)

    async def update_slot(
        self,
        slot_id: int,
        day_of_week: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        is_active: Optional[bool] = None,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> AvailableSlot:
        """
        Update an existing available slot.

        Args:
            slot_id: Slot ID
            day_of_week: New day of week (0=Monday, 6=Sunday)
            start_time: New start time in "HH:MM" format
            end_time: New end time in "HH:MM" format
            is_active: New active status
            actor_id: ID of user updating the slot
            ip_address: IP address of the request

        Returns:
            Updated slot entity

        Raises:
            SlotValidationError: If validation fails or slot not found
        """
        # Validate slot exists
        slot = await self.slot_repo.get_slot_by_id(slot_id)
        if not slot:
            raise SlotValidationError("Slot not found", "SLOT_NOT_FOUND")

        # Validate day_of_week if provided
        if day_of_week is not None and not 0 <= day_of_week <= 6:
            raise SlotValidationError(
                "day_of_week must be between 0 (Monday) and 6 (Sunday)",
                "INVALID_DAY_OF_WEEK",
            )

        # Validate time format if provided
        if start_time is not None:
            try:
                start_hour, start_minute = map(int, start_time.split(":"))
                if not (0 <= start_hour <= 23 and 0 <= start_minute <= 59):
                    raise SlotValidationError("Invalid start time", "INVALID_START_TIME")
            except ValueError:
                raise SlotValidationError(
                    "Time must be in 'HH:MM' format",
                    "INVALID_TIME_FORMAT",
                )

        if end_time is not None:
            try:
                end_hour, end_minute = map(int, end_time.split(":"))
                if not (0 <= end_hour <= 23 and 0 <= end_minute <= 59):
                    raise SlotValidationError("Invalid end time", "INVALID_END_TIME")
            except ValueError:
                raise SlotValidationError(
                    "Time must be in 'HH:MM' format",
                    "INVALID_TIME_FORMAT",
                )

        # If both times are provided, validate range
        slot_start = start_time if start_time is not None else slot.start_time
        slot_end = end_time if end_time is not None else slot.end_time
        if slot_start >= slot_end:
            raise SlotValidationError(
                "start_time must be before end_time",
                "INVALID_TIME_RANGE",
            )

        return await self.slot_repo.update_slot(
            slot_id=slot_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            is_active=is_active,
            actor_id=actor_id,
            ip_address=ip_address,
        )

    async def delete_slot(
        self,
        slot_id: int,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Delete an available slot.

        Args:
            slot_id: Slot ID
            actor_id: ID of user deleting the slot
            ip_address: IP address of the request

        Returns:
            True if deleted, False if not found

        Raises:
            SlotValidationError: If slot not found
        """
        # Validate slot exists
        slot = await self.slot_repo.get_slot_by_id(slot_id)
        if not slot:
            raise SlotValidationError("Slot not found", "SLOT_NOT_FOUND")

        return await self.slot_repo.delete_slot(
            slot_id=slot_id,
            actor_id=actor_id,
            ip_address=ip_address,
        )

    async def check_availability(
        self,
        tutor_id: int,
        day_of_week: int,
        time: str,
    ) -> bool:
        """
        Check if tutor is available at a specific time.

        Args:
            tutor_id: Tutor's ID
            day_of_week: Day of week (0=Monday, 6=Sunday)
            time: Time in "HH:MM" format

        Returns:
            True if tutor is available, False otherwise

        Raises:
            SlotValidationError: If validation fails
        """
        # Validate tutor exists
        tutor = await self.tutor_repo.find_by_id(tutor_id)
        if not tutor:
            raise SlotValidationError("Tutor not found", "TUTOR_NOT_FOUND")

        # Validate day_of_week range
        if not 0 <= day_of_week <= 6:
            raise SlotValidationError(
                "day_of_week must be between 0 (Monday) and 6 (Sunday)",
                "INVALID_DAY_OF_WEEK",
            )

        # Validate time format
        try:
            hour, minute = map(int, time.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise SlotValidationError("Invalid time", "INVALID_TIME")
        except ValueError:
            raise SlotValidationError(
                "Time must be in 'HH:MM' format",
                "INVALID_TIME_FORMAT",
            )

        return await self.slot_repo.check_availability(
            tutor_id=tutor_id,
            day_of_week=day_of_week,
            time=time,
        )
