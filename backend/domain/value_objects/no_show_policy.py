"""No-show policy value object with business logic."""
from dataclasses import dataclass
from enum import Enum
from typing import Literal


class NoShowPolicy(str, Enum):
    """Tutor's no-show policy types."""

    FULL_DEDUCTION = "FULL_DEDUCTION"
    ONE_FREE = "ONE_FREE"
    NONE = "NONE"


@dataclass(frozen=True)
class NoShowPolicyConfig:
    """Value object for no-show policy configuration."""

    policy_type: NoShowPolicy
    description: str

    def __str__(self) -> str:
        return self.description

    def is_billable_on_no_show(
        self,
        monthly_no_show_count: int,
        is_first_no_show_of_month: bool,
    ) -> bool:
        """Determine if a no-show session is billable.

        Args:
            monthly_no_show_count: Total no-shows in the current month
            is_first_no_show_of_month: Whether this is the first no-show

        Returns:
            True if the no-show should be billed, False otherwise
        """
        if self.policy_type == NoShowPolicy.FULL_DEDUCTION:
            # All no-shows are billable
            return True

        if self.policy_type == NoShowPolicy.ONE_FREE:
            # First no-show of the month is free
            return not is_first_no_show_of_month

        if self.policy_type == NoShowPolicy.NONE:
            # Manual handling - not billable
            return False

        return False

    def get_free_no_show_allowance(self) -> int:
        """Get the number of free no-shows allowed per month.

        Returns:
            Number of free no-shows (0, 1, or None for manual handling)
        """
        if self.policy_type == NoShowPolicy.FULL_DEDUCTION:
            return 0
        if self.policy_type == NoShowPolicy.ONE_FREE:
            return 1
        if self.policy_type == NoShowPolicy.NONE:
            return -1  # Special value indicating manual handling
        return 0


# Predefined no-show policies
FULL_DEDUCTION_POLICY = NoShowPolicyConfig(
    NoShowPolicy.FULL_DEDUCTION,
    "결석 시 수업료 전액 차감 (무단 결석으로 처리됩니다)"
)

ONE_FREE_POLICY = NoShowPolicyConfig(
    NoShowPolicy.ONE_FREE,
    "월 1회 무결석 허용, 이후 결석 시 전액 차감"
)

NONE_POLICY = NoShowPolicyConfig(
    NoShowPolicy.NONE,
    "별도 협의 (튜터와 직접 상담 필요)"
)


def get_policy_by_type(policy_type: str) -> NoShowPolicyConfig:
    """Get a NoShowPolicyConfig by its policy type string.

    Args:
        policy_type: The policy type string

    Returns:
        The corresponding NoShowPolicyConfig

    Raises:
        ValueError: If the policy type is invalid
    """
    try:
        policy_enum = NoShowPolicy(policy_type)
    except ValueError:
        raise ValueError(f"Invalid no-show policy type: {policy_type}")

    if policy_enum == NoShowPolicy.FULL_DEDUCTION:
        return FULL_DEDUCTION_POLICY
    if policy_enum == NoShowPolicy.ONE_FREE:
        return ONE_FREE_POLICY
    if policy_enum == NoShowPolicy.NONE:
        return NONE_POLICY

    raise ValueError(f"Unknown no-show policy type: {policy_type}")
