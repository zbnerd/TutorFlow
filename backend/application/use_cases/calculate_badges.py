"""Badge calculation use cases for tutor recognition."""
from dataclasses import dataclass
from typing import Optional

from domain.entities.badge import Badge, create_badges
from domain.ports import ReviewRepositoryPort


@dataclass
class TutorBadgeStats:
    """Statistics for badge calculation."""

    total_reviews: int
    avg_rating: float
    reply_rate: float


@dataclass
class BadgeCalculationResult:
    """Result of badge calculation for a tutor."""

    tutor_id: int
    badges_earned: list[Badge]
    stats: TutorBadgeStats


class CalculateBadgesUseCase:
    """Use case for calculating tutor badges based on review statistics."""

    def __init__(
        self,
        review_repo: ReviewRepositoryPort,
        popular_tutor_min_reviews: int = 10,
        popular_tutor_min_rating: float = 4.5,
        best_tutor_min_reviews: int = 30,
        best_tutor_min_rating: float = 4.8,
        reply_king_response_rate: float = 80.0,
    ):
        """
        Initialize with review repository and configurable badge thresholds.

        Args:
            review_repo: Review repository for fetching statistics
            popular_tutor_min_reviews: Minimum reviews for Popular Tutor badge
            popular_tutor_min_rating: Minimum rating for Popular Tutor badge
            best_tutor_min_reviews: Minimum reviews for Best Tutor badge
            best_tutor_min_rating: Minimum rating for Best Tutor badge
            reply_king_response_rate: Minimum reply rate for Response King badge
        """
        self.review_repo = review_repo

        # Create badges with configured thresholds
        self.all_badges, self.badge_map = create_badges(
            popular_tutor_min_reviews=popular_tutor_min_reviews,
            popular_tutor_min_rating=popular_tutor_min_rating,
            best_tutor_min_reviews=best_tutor_min_reviews,
            best_tutor_min_rating=best_tutor_min_rating,
            reply_king_response_rate=reply_king_response_rate,
        )

    async def calculate_tutor_badges(self, tutor_id: int) -> BadgeCalculationResult:
        """
        Calculate badges for a specific tutor.

        Args:
            tutor_id: Tutor ID

        Returns:
            BadgeCalculationResult with earned badges and statistics
        """
        # Get statistics from repository
        stats_dict = await self.review_repo.get_tutor_stats(tutor_id)
        stats = TutorBadgeStats(
            total_reviews=stats_dict.get("total_reviews", 0),
            avg_rating=stats_dict.get("average_rating", 0.0),
            reply_rate=stats_dict.get("reply_rate", 0.0),
        )

        # Check which badges the tutor qualifies for
        badges_earned = []
        for badge in self.all_badges:
            if badge.qualifies(
                total_reviews=stats.total_reviews,
                avg_rating=stats.avg_rating,
                reply_rate=stats.reply_rate,
            ):
                badges_earned.append(badge)

        return BadgeCalculationResult(
            tutor_id=tutor_id,
            badges_earned=badges_earned,
            stats=stats,
        )

    async def calculate_all_tutors_badges(
        self,
        tutor_ids: list[int],
    ) -> list[BadgeCalculationResult]:
        """
        Calculate badges for multiple tutors.

        Args:
            tutor_ids: List of tutor IDs

        Returns:
            List of BadgeCalculationResult for each tutor
        """
        results = []
        for tutor_id in tutor_ids:
            result = await self.calculate_tutor_badges(tutor_id)
            results.append(result)

        return results

    def get_badge_by_id(self, badge_id: str) -> Optional[Badge]:
        """
        Get a badge by its ID.

        Args:
            badge_id: Badge identifier (e.g., "popular_tutor")

        Returns:
            Badge if found, None otherwise
        """
        return self.badge_map.get(badge_id)

    def get_all_available_badges(self) -> list[Badge]:
        """
        Get all available badge definitions.

        Returns:
            List of all Badge objects
        """
        return self.all_badges.copy()
