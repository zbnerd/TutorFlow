"""Badge domain entities for tutor recognition."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Badge:
    """Represents a achievement badge that tutors can earn."""

    id: str  # Internal identifier (e.g., "popular_tutor")
    name: str  # Display name (e.g., "인기 튜터")
    description: str
    threshold_reviews: int
    threshold_rating: Optional[float] = None
    threshold_reply_rate: Optional[float] = None  # Percentage

    def qualifies(
        self,
        total_reviews: int,
        avg_rating: float,
        reply_rate: float,
    ) -> bool:
        """Check if tutor qualifies for this badge."""
        # Check review threshold
        if total_reviews < self.threshold_reviews:
            return False

        # Check rating threshold if applicable
        if self.threshold_rating is not None and avg_rating < self.threshold_rating:
            return False

        # Check reply rate threshold if applicable
        if self.threshold_reply_rate is not None and reply_rate < self.threshold_reply_rate:
            return False

        return True


def create_badges(
    popular_tutor_min_reviews: int = 10,
    popular_tutor_min_rating: float = 4.5,
    best_tutor_min_reviews: int = 30,
    best_tutor_min_rating: float = 4.8,
    reply_king_response_rate: float = 80.0,
) -> tuple[list[Badge], dict[str, Badge]]:
    """
    Create badge instances with configurable thresholds.

    Args:
        popular_tutor_min_reviews: Minimum reviews for Popular Tutor badge
        popular_tutor_min_rating: Minimum rating for Popular Tutor badge
        best_tutor_min_reviews: Minimum reviews for Best Tutor badge
        best_tutor_min_rating: Minimum rating for Best Tutor badge
        reply_king_response_rate: Minimum reply rate for Response King badge

    Returns:
        Tuple of (ALL_BADGES list, BADGE_MAP dict)
    """
    # Predefined badges with configurable thresholds
    POPULAR_TUTOR = Badge(
        id="popular_tutor",
        name="인기 튜터",
        description="10개 이상의 리뷰와 4.5점 이상의 평균 평점을 받은 튜터",
        threshold_reviews=popular_tutor_min_reviews,
        threshold_rating=popular_tutor_min_rating,
    )

    BEST_TUTOR = Badge(
        id="best_tutor",
        name="베스트 튜터",
        description="30개 이상의 리뷰와 4.8점 이상의 평균 평점을 받은 튜터",
        threshold_reviews=best_tutor_min_reviews,
        threshold_rating=best_tutor_min_rating,
    )

    RESPONSE_KING = Badge(
        id="response_king",
        name="답변왕",
        description="리뷰 답변률 80% 이상을 달성한 튜터",
        threshold_reviews=0,  # No minimum reviews required
        threshold_reply_rate=reply_king_response_rate,
    )

    # All available badges
    all_badges = [
        POPULAR_TUTOR,
        BEST_TUTOR,
        RESPONSE_KING,
    ]

    # Badge lookup by ID
    badge_map = {badge.id: badge for badge in all_badges}

    return all_badges, badge_map


# Default badges with default thresholds
ALL_BADGES, BADGE_MAP = create_badges()
