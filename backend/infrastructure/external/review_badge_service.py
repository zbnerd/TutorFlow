"""Review badge calculation service for daily batch job."""
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from infrastructure.persistence.models import ReviewModel, TutorModel
from domain.entities import Review


class ReviewBadgeService:
    """Service for calculating and updating tutor review badges."""

    # Badge thresholds
    POPULAR_TUTOR_MIN_REVIEWS = 10
    POPULAR_TUTOR_MIN_RATING = 4.5
    BEST_TUTOR_MIN_REVIEWS = 30
    BEST_TUTOR_MIN_RATING = 4.8
    RESPONSE_KING_REPLY_RATE = 80  # percentage

    # Badge display names (Korean)
    BADGE_NAMES = {
        "popular_tutor": "인기 튜터",  # Popular Tutor
        "best_tutor": "베스트 튜터",  # Best Tutor
        "response_king": "답변왕",  # Response King
    }

    def __init__(self, session: AsyncSession):
        """Initialize badge service with database session."""
        self.session = session

    async def calculate_badges_for_tutor(self, tutor_id: int) -> Dict[str, any]:
        """
        Calculate badges for a specific tutor.

        Args:
            tutor_id: Tutor ID

        Returns:
            Dict with badges list and statistics
        """
        # Get review statistics
        stats = await self._get_tutor_stats(tutor_id)

        # Calculate badges
        badges = []

        if stats["total_reviews"] >= self.POPULAR_TUTOR_MIN_REVIEWS:
            if stats["avg_rating"] >= self.POPULAR_TUTOR_MIN_RATING:
                badges.append(self.BADGE_NAMES["popular_tutor"])

        if stats["total_reviews"] >= self.BEST_TUTOR_MIN_REVIEWS:
            if stats["avg_rating"] >= self.BEST_TUTOR_MIN_RATING:
                badges.append(self.BADGE_NAMES["best_tutor"])

        if stats["reply_rate"] >= self.RESPONSE_KING_REPLY_RATE:
            badges.append(self.BADGE_NAMES["response_king"])

        return {
            "tutor_id": tutor_id,
            "badges": badges,
            "total_reviews": stats["total_reviews"],
            "avg_rating": stats["avg_rating"],
            "reply_rate": stats["reply_rate"],
        }

    async def calculate_all_tutor_badges(self) -> List[Dict[str, any]]:
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
        badges_list = []
        for tutor_id in tutor_ids:
            badges_info = await self.calculate_badges_for_tutor(tutor_id)
            badges_list.append(badges_info)

        return badges_list

    async def _get_tutor_stats(self, tutor_id: int) -> Dict[str, any]:
        """
        Get review statistics for a tutor.

        Args:
            tutor_id: Tutor ID

        Returns:
            Dict with total_reviews, avg_rating, reply_count, reply_rate
        """
        # Total reviews and average rating
        result = await self.session.execute(
            select(
                func.count(ReviewModel.id).label("total"),
                func.avg(ReviewModel.overall_rating).label("avg_rating"),
            ).where(ReviewModel.tutor_id == tutor_id)
        )
        stats = result.one()
        total_reviews = stats.total or 0
        avg_rating = float(stats.avg_rating or 0)

        # Reply statistics
        reply_result = await self.session.execute(
            select(
                func.count(ReviewModel.id).label("total"),
                func.sum(
                    func.case(
                        (ReviewModel.tutor_reply.isnot(None), 1),
                        else_=0,
                    )
                ).label("replied"),
            ).where(ReviewModel.tutor_id == tutor_id)
        )
        reply_stats = reply_result.one()
        reply_count = reply_stats.replied or 0
        reply_rate = (reply_count / reply_stats.total * 100) if reply_stats.total > 0 else 0

        return {
            "total_reviews": total_reviews,
            "avg_rating": avg_rating,
            "reply_count": reply_count,
            "reply_rate": reply_rate,
        }


async def run_daily_badge_calculation(session: AsyncSession) -> Dict[str, any]:
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
