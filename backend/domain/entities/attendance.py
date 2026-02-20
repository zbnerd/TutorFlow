"""Attendance domain entity."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal


class AttendanceStatus(str, Enum):
    """Attendance status enumeration."""

    ATTENDED = "ATTENDED"
    NO_SHOW = "NO_SHOW"
    CANCELLED = "CANCELLED"


@dataclass
class Attendance:
    """Attendance record for a booking session.

    Tracks whether a student attended their scheduled session.
    """

    id: int | None = None
    booking_session_id: int | None = None
    status: AttendanceStatus = AttendanceStatus.ATTENDED
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def mark_attended(self, notes: str | None = None) -> "Attendance":
        """Mark the session as attended."""
        self.status = AttendanceStatus.ATTENDED
        if notes:
            self.notes = notes
        return self

    def mark_no_show(self, notes: str | None = None) -> "Attendance":
        """Mark the session as no-show."""
        self.status = AttendanceStatus.NO_SHOW
        if notes:
            self.notes = notes
        return self

    def cancel(self, reason: str | None = None) -> "Attendance":
        """Mark the session as cancelled."""
        self.status = AttendanceStatus.CANCELLED
        if reason:
            self.notes = reason
        return self

    def is_attended(self) -> bool:
        """Check if the student attended."""
        return self.status == AttendanceStatus.ATTENDED

    def is_no_show(self) -> bool:
        """Check if the student was a no-show."""
        return self.status == AttendanceStatus.NO_SHOW

    def is_cancelled(self) -> bool:
        """Check if the session was cancelled."""
        return self.status == AttendanceStatus.CANCELLED

    def is_billable(self, no_show_policy: "NoShowPolicyType") -> bool:
        """Determine if this session is billable based on status and policy.

        Args:
            no_show_policy: The tutor's no-show policy

        Returns:
            True if the session should be billed, False otherwise
        """
        if self.status == AttendanceStatus.ATTENDED:
            return True
        if self.status == AttendanceStatus.CANCELLED:
            return False
        # NO_SHOW status - depends on policy
        if no_show_policy == NoShowPolicyType.FULL_DEDUCTION:
            return True  # No-show is billed
        if no_show_policy == NoShowPolicyType.ONE_FREE:
            # This is handled at the booking level (monthly count)
            # Default to True here, use case layer will apply free pass logic
            return True
        if no_show_policy == NoShowPolicyType.NONE:
            return False  # Manual handling
        return False


@dataclass(frozen=True)
class NoShowPolicyType:
    """Value object for no-show policy types."""

    policy_type: Literal["FULL_DEDUCTION", "ONE_FREE", "NONE"]
    description: str

    def __str__(self) -> str:
        return self.description


# Predefined no-show policies
FULL_DEDUCTION = NoShowPolicyType(
    "FULL_DEDUCTION",
    "결석 시 수업료 전액 차감 (무단 결석으로 처리됩니다)"
)

ONE_FREE = NoShowPolicyType(
    "ONE_FREE",
    "월 1회 무결석 허용, 이후 결석 시 전액 차감"
)

NONE = NoShowPolicyType(
    "NONE",
    "별도 협의 (튜터와 직접 상담 필요)"
)
