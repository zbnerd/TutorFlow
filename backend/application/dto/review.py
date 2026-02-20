"""Review DTOs for request/response handling."""
from datetime import datetime
import re
from pydantic import BaseModel, Field, field_validator


class ReviewCreateRequest(BaseModel):
    """Review creation request."""

    booking_id: int = Field(..., description="Booking ID to review")
    overall_rating: int = Field(..., ge=1, le=5, description="Overall rating 1-5")
    kindness_rating: int = Field(default=5, ge=1, le=5, description="Kindness rating 1-5")
    preparation_rating: int = Field(default=5, ge=1, le=5, description="Preparation rating 1-5")
    improvement_rating: int = Field(default=5, ge=1, le=5, description="Improvement rating 1-5")
    punctuality_rating: int = Field(default=5, ge=1, le=5, description="Punctuality rating 1-5")
    content: str = Field(..., min_length=10, max_length=2000, description="Review content")
    is_anonymous: bool = Field(default=True, description="Post review anonymously")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate content for prohibited content."""
        # Basic profanity filter (Korean)
        profanity_patterns = ["시발", "병신", "미친", "개새끼", "섹스", " porn", "카톡:", "010-"]
        v_lower = v.lower()
        for pattern in profanity_patterns:
            if pattern in v_lower:
                raise ValueError(f"리뷰 내용에 부적절한 표현이 포함되어 있습니다.")

        # Check for phone numbers
        phone_pattern = r"(\d{2,3}-?\d{3,4}-?\d{4}|010\d{8})"
        if re.search(phone_pattern, v):
            raise ValueError("리뷰에 연락처를 포함할 수 없습니다.")

        return v


class ReviewUpdateRequest(BaseModel):
    """Review update request."""

    overall_rating: int | None = Field(None, ge=1, le=5)
    kindness_rating: int | None = Field(None, ge=1, le=5)
    preparation_rating: int | None = Field(None, ge=1, le=5)
    improvement_rating: int | None = Field(None, ge=1, le=5)
    punctuality_rating: int | None = Field(None, ge=1, le=5)
    content: str | None = Field(None, min_length=10, max_length=2000)
    is_anonymous: bool | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str | None) -> str | None:
        """Validate content for prohibited content."""
        if v is None:
            return v
        # Basic profanity filter (Korean)
        profanity_patterns = ["시발", "병신", "미친", "개새끼", "섹스", " porn", "카톡:", "010-"]
        v_lower = v.lower()
        for pattern in profanity_patterns:
            if pattern in v_lower:
                raise ValueError(f"리뷰 내용에 부적절한 표현이 포함되어 있습니다.")

        # Check for phone numbers
        phone_pattern = r"(\d{2,3}-?\d{3,4}-?\d{4}|010\d{8})"
        if re.search(phone_pattern, v):
            raise ValueError("리뷰에 연락처를 포함할 수 없습니다.")

        return v


class ReviewReplyRequest(BaseModel):
    """Tutor reply request."""

    reply: str = Field(..., min_length=1, max_length=1000, description="Tutor's reply to review")


class ReviewReportRequest(BaseModel):
    """Review report request."""

    reason: str = Field(..., description="Reason for report: spam, abuse, false_info")
    description: str | None = Field(None, max_length=1000, description="Additional details")

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        """Validate report reason."""
        valid_reasons = ["spam", "abuse", "false_info"]
        if v not in valid_reasons:
            raise ValueError(f"사유는 다음 중 하나여야 합니다: {', '.join(valid_reasons)}")
        return v


class ReviewResponse(BaseModel):
    """Review response."""

    id: int
    booking_id: int
    tutor_id: int
    student_id: int
    overall_rating: int
    kindness_rating: int
    preparation_rating: int
    improvement_rating: int
    punctuality_rating: int
    content: str
    is_anonymous: bool
    tutor_reply: str | None
    tutor_replied_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # Additional fields for display
    student_name: str | None = None  # Only if not anonymous
    tutor_badge: str | None = None  # Popular Tutor, Best Tutor, Response King


class TutorReviewsResponse(BaseModel):
    """Tutor reviews response with badge info."""

    reviews: list[ReviewResponse]
    total_count: int
    avg_rating: float
    total_reviews: int
    badges: list[str]  # Popular Tutor, Best Tutor, Response King


class ReviewListFilters(BaseModel):
    """Review list filters."""

    tutor_id: int | None = None
    min_rating: float | None = Field(None, ge=1, le=5)
    has_photo: bool | None = None  # For future photo review feature
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
