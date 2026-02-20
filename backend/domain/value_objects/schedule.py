"""Schedule value objects for booking validation."""
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import List


@dataclass(frozen=True)
class TimeRange:
    """Value object representing a time range."""
    start_time: time
    end_time: time

    def __post_init__(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")

    def duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        return int((end - start).total_seconds() / 60)

    def overlaps(self, other: "TimeRange") -> bool:
        """Check if this time range overlaps with another."""
        return not (self.end_time <= other.start_time or self.start_time >= other.end_time)


@dataclass
class ScheduleSlot:
    """Value object for a scheduled time slot."""
    date: datetime
    time_range: TimeRange

    def is_future(self) -> bool:
        """Check if this slot is in the future (at least 24 hours away)."""
        slot_start = datetime.combine(self.date, self.time_range.start_time)
        min_booking_time = datetime.now() + timedelta(hours=24)
        return slot_start >= min_booking_time

    def to_booking_session_time(self) -> str:
        """Convert to booking session time format (HH:MM)."""
        return self.time_range.start_time.strftime("%H:%M")


def find_schedule_conflicts(
    existing_slots: List[ScheduleSlot],
    new_slots: List[ScheduleSlot],
) -> List[ScheduleSlot]:
    """
    Find conflicting time slots between existing and new schedules.

    Args:
        existing_slots: Currently booked slots
        new_slots: Slots to check for conflicts

    Returns:
        List of conflicting slots from new_slots
    """
    conflicts = []

    for new_slot in new_slots:
        for existing_slot in existing_slots:
            if new_slot.date == existing_slot.date:
                if new_slot.time_range.overlaps(existing_slot.time_range):
                    conflicts.append(new_slot)
                    break

    return conflicts
