"""Settlement domain entity."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SettlementStatus(str, Enum):
    """Settlement status enumeration.

    PENDING: Settlement calculated but not yet paid
    COMPLETED: Settlement paid to tutor
    FAILED: Settlement payment failed
    """

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Settlement:
    """Monthly settlement for tutors.

    Aggregates completed sessions from a specific month and calculates
    the net amount to be paid to the tutor after deducting fees.
    """

    id: int | None = None
    tutor_id: int | None = None
    year_month: str | None = None  # "2024-01"
    total_sessions: int = 0
    total_amount: "Money | None" = None
    platform_fee: "Money | None" = None  # 5% platform fee
    pg_fee: "Money | None" = None  # 3% PG fee
    net_amount: "Money | None" = None
    is_paid: bool = False
    paid_at: datetime | None = None
    created_at: datetime | None = None

    def calculate_net_amount(self) -> None:
        """Calculate net amount after deducting all fees.

        Formula: total_amount - platform_fee - pg_fee
        """
        if self.total_amount and self.platform_fee and self.pg_fee:
            from domain.entities import Money

            # Import Money locally to avoid circular import
            fees = self.total_amount.subtract(self.platform_fee)
            self.net_amount = fees.subtract(self.pg_fee)

    def mark_as_paid(self, paid_at: datetime | None = None) -> None:
        """Mark settlement as paid."""
        from datetime import datetime as dt

        self.is_paid = True
        self.paid_at = paid_at or dt.utcnow()

    def mark_as_failed(self) -> None:
        """Mark settlement as failed."""
        self.is_paid = False
        self.paid_at = None

    def is_pending(self) -> bool:
        """Check if settlement is pending payment."""
        return not self.is_paid

    def is_completed(self) -> bool:
        """Check if settlement is completed."""
        return self.is_paid and self.paid_at is not None
