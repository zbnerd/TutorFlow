"""Value objects for domain concepts."""
from dataclasses import dataclass
from datetime import time
from typing import Literal


@dataclass
class Schedule:
    """Value object representing a time schedule."""
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: time
    end_time: time

    def __post_init__(self):
        if not 0 <= self.day_of_week <= 6:
            raise ValueError("day_of_week must be 0-6")
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")


@dataclass(frozen=True)
class NoShowPolicy:
    """Value object for no-show policies."""
    policy_type: Literal["full_deduction", "one_free", "none"]
    description: str

    def __str__(self) -> str:
        return self.description


# Predefined no-show policies
FULL_DEDUCTION = NoShowPolicy(
    "full_deduction",
    "결석 시 수업료 전액 차감 (무단 결석으로 처리됩니다)"
)

ONE_FREE = NoShowPolicy(
    "one_free",
    "월 1회 무결석 허용, 이후 결석 시 전액 차감"
)

NONE = NoShowPolicy(
    "none",
    "별도 협의 (튜터와 직접 상담 필요)"
)


@dataclass
class TokenPair:
    """Value object for access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass
class OAuthUserInfo:
    """Value object for OAuth user information."""

    id: str
    email: str | None
    name: str
    profile_image_url: str | None = None
    phone: str | None = None
