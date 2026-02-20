"""Review badge service - delegates to use case for badge calculation.

This service is now a thin wrapper that fetches data from the database
and delegates badge calculation logic to the application layer.
"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.persistence.models import TutorModel
from infrastructure.persistence.repositories.review_repository import ReviewRepository
from application.use_cases.calculate_badges import CalculateBadgesUseCase
from config import settings


class ReviewBadgeService:
    """Service for calculating tutor badges using use case layer."""

    def __init__(self, session: AsyncSession):
        """Initialize badge service with database session."""
        self.session = session
        self.review_repo = ReviewRepository(session)
        self.badge_use_case = CalculateBadgesUseCase(
            self.review_repo,
            popular_tutor_min_reviews=settings.BADGE_POPULAR_TUTOR_MIN_REVIEWS,
            popular_tutor_min_rating=settings.BADGE_POPULAR_TUTOR_MIN_RATING,
            best_tutor_min_reviews=settings.BADGE_BEST_TUTOR_MIN_REVIEWS,
            best_tutor_min_rating=settings.BADGE_BEST_TUTOR_MIN_RATING,
            reply_king_response_rate=settings.BADGE_REPLY_KING_RESPONSE_RATE,
        )

    async def calculate_badges_for_tutor(self, tutor_id: int) -> dict:
        """
        Calculate badges for a specific tutor.

        Args:
            tutor_id: Tutor ID

        Returns:
            Dict with badges list and statistics
        """
        result = await self.badge_use_case.calculate_tutor_badges(tutor_id)

        return {
            "tutor_id": tutor_id,
            "badges": [badge.name for badge in result.badges_earned],
            "total_reviews": result.stats.total_reviews,
            "avg_rating": result.stats.avg_rating,
            "reply_rate": result.stats.reply_rate,
        }

    async def calculate_all_tutor_badges(self) -> List[dict]:
        """
        Calculate badges for all approved tutors.

        This is intended to be run as a daily batch job.

        Returns:
            List of tutor badge information
        """
        # Get all approved tutor IDs
        result = await self.session.execute(
            select(TutorModel.id)
            .where(TutorModel.is_approved == True)
        )
        tutor_ids = [row[0] for row in result.fetchall()]

        # Calculate badges for each tutor
        results = await self.badge_use_case.calculate_all_tutors_badges(tutor_ids)

        return [
            {
                "tutor_id": r.tutor_id,
                "badges": [badge.name for badge in r.badges_earned],
                "total_reviews": r.stats.total_reviews,
                "avg_rating": r.stats.avg_rating,
                "reply_rate": r.stats.reply_rate,
            }
            for r in results
        ]


async def run_daily_badge_calculation(session: AsyncSession) -> dict:
    """
    Run daily badge calculation for all tutors.

    This is the main entry point for the daily batch job.

    Args:
        session: Database session

    Returns:
        Summary of badge calculation results
    """
    service = ReviewBadgeService(session)
    results = await service.calculate_all_tutor_badges()

    # Count badges
    popular_count = sum(1 for r in results if "인기 튜터" in r["badges"])
    best_count = sum(1 for r in results if "베스트 튜터" in r["badges"])
    response_king_count = sum(1 for r in results if "답변왕" in r["badges"])

    return {
        "total_tutors": len(results),
        "popular_tutors": popular_count,
        "best_tutors": best_count,
        "response_kings": response_king_count,
        "results": results,
    }
