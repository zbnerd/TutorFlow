"""Review use cases for review management."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import re

from domain.entities import Review, ReviewReport
from domain.ports import ReviewRepositoryPort


@dataclass
class ReviewUseCases:
    """Review management use cases."""

    review_repo: ReviewRepositoryPort

    async def create_review(
        self,
        booking_id: int,
        student_id: int,
        overall_rating: int,
        kindness_rating: int,
        preparation_rating: int,
        improvement_rating: int,
        punctuality_rating: int,
        content: str,
        is_anonymous: bool,
    ) -> Review:
        """
        Create a new review with validation.

        Validation:
        1. Verified payment only (payment_status == PAID)
        2. At least 1 completed session
        3. No existing review for this booking
        4. Content moderation (profanity, phone, ads)
        5. Can only update within 7 days

        Args:
            booking_id: Booking ID to review
            student_id: Student creating the review
            All review fields

        Returns:
            Created Review entity

        Raises:
            ValueError: If validation fails
        """
        # Check if user can create review (also validates booking exists and gets tutor_id)
        can_create, reason, tutor_id = await self.review_repo.can_create_review(
            booking_id, student_id
        )
        if not can_create:
            raise ValueError(reason)

        # Content moderation
        self._moderate_content(content)

        # Create review
        review = Review(
            booking_id=booking_id,
            tutor_id=tutor_id,
            student_id=student_id,
            overall_rating=overall_rating,
            kindness_rating=kindness_rating,
            preparation_rating=preparation_rating,
            improvement_rating=improvement_rating,
            punctuality_rating=punctuality_rating,
            content=content,
            is_anonymous=is_anonymous,
        )

        return await self.review_repo.save(review)

    async def update_review(
        self,
        review_id: int,
        student_id: int,
        overall_rating: int | None = None,
        kindness_rating: int | None = None,
        preparation_rating: int | None = None,
        improvement_rating: int | None = None,
        punctuality_rating: int | None = None,
        content: str | None = None,
        is_anonymous: bool | None = None,
    ) -> Review:
        """
        Update an existing review.

        Can only update within 7 days of creation.

        Args:
            review_id: Review ID to update
            student_id: Current user ID (must match review's student_id)
            Other fields to update

        Returns:
            Updated Review entity

        Raises:
            ValueError: If validation fails
        """
        review = await self.review_repo.find_by_id(review_id)
        if not review:
            raise ValueError("리뷰를 찾을 수 없습니다.")

        # Verify ownership
        if review.student_id != student_id:
            raise ValueError("본인이 작성한 리뷰만 수정할 수 있습니다.")

        # Check 7-day update window
        if review.created_at:
            time_diff = datetime.utcnow() - review.created_at
            if time_diff > timedelta(days=7):
                raise ValueError("작성 후 7일이 지난 리뷰는 수정할 수 없습니다.")

        # Update fields
        if overall_rating is not None:
            review.overall_rating = overall_rating
        if kindness_rating is not None:
            review.kindness_rating = kindness_rating
        if preparation_rating is not None:
            review.preparation_rating = preparation_rating
        if improvement_rating is not None:
            review.improvement_rating = improvement_rating
        if punctuality_rating is not None:
            review.punctuality_rating = punctuality_rating
        if content is not None:
            self._moderate_content(content)
            review.content = content
        if is_anonymous is not None:
            review.is_anonymous = is_anonymous

        return await self.review_repo.save(review)

    async def delete_review(self, review_id: int, student_id: int) -> bool:
        """
        Delete a review.

        Can only delete within 7 days of creation.

        Args:
            review_id: Review ID to delete
            student_id: Current user ID (must match review's student_id)

        Returns:
            True if deleted

        Raises:
            ValueError: If validation fails
        """
        review = await self.review_repo.find_by_id(review_id)
        if not review:
            raise ValueError("리뷰를 찾을 수 없습니다.")

        # Verify ownership
        if review.student_id != student_id:
            raise ValueError("본인이 작성한 리뷰만 삭제할 수 있습니다.")

        # Check 7-day delete window
        if review.created_at:
            time_diff = datetime.utcnow() - review.created_at
            if time_diff > timedelta(days=7):
                raise ValueError("작성 후 7일이 지난 리뷰는 삭제할 수 없습니다.")

        # Delete review (soft delete by setting content to empty)
        review.content = "[삭제된 리뷰입니다]"
        await self.review_repo.save(review)

        return True

    async def add_tutor_reply(self, review_id: int, tutor_id: int, reply: str) -> Review:
        """
        Add tutor reply to review.

        Args:
            review_id: Review ID
            tutor_id: Tutor ID (must match review's tutor_id)
            reply: Reply content

        Returns:
            Updated Review entity

        Raises:
            ValueError: If validation fails
        """
        review = await self.review_repo.find_by_id(review_id)
        if not review:
            raise ValueError("리뷰를 찾을 수 없습니다.")

        # Verify tutor ownership
        if review.tutor_id != tutor_id:
            raise ValueError("본인에게 작성된 리뷰에만 답글을 달 수 있습니다.")

        # Add reply
        review.tutor_reply = reply
        review.tutor_replied_at = datetime.utcnow()

        return await self.review_repo.save(review)

    async def report_review(
        self,
        review_id: int,
        reporter_id: int,
        reason: str,
        description: str | None = None,
    ) -> ReviewReport:
        """
        Report a review for moderation.

        Args:
            review_id: Review ID to report
            reporter_id: User ID reporting the review
            reason: Reason for report (spam, abuse, false_info)
            description: Additional details

        Returns:
            Created ReviewReport entity

        Raises:
            ValueError: If validation fails
        """
        review = await self.review_repo.find_by_id(review_id)
        if not review:
            raise ValueError("리뷰를 찾을 수 없습니다.")

        # Cannot report own review
        if review.student_id == reporter_id:
            raise ValueError("본인이 작성한 리뷰는 신고할 수 없습니다.")

        # Create report
        report = ReviewReport(
            review_id=review_id,
            reporter_id=reporter_id,
            reason=reason,
            description=description,
            is_processed=False,
        )

        return await self.review_repo.save_report(report)

    async def get_tutor_reviews(
        self,
        tutor_id: int,
        min_rating: float | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Review], dict]:
        """
        Get reviews for a tutor with badge information.

        Args:
            tutor_id: Tutor ID
            min_rating: Minimum rating filter
            offset: Pagination offset
            limit: Max results

        Returns:
            Tuple of (list of reviews, badge info dict)
        """
        reviews = await self.review_repo.list_by_tutor(
            tutor_id=tutor_id,
            min_rating=min_rating,
            offset=offset,
            limit=limit,
        )

        # Get tutor stats for badge calculation
        stats = await self.review_repo.get_tutor_stats(tutor_id)
        badges = self._calculate_badges(stats)

        return reviews, {
            "total_count": len(reviews),
            "avg_rating": stats["average_rating"],
            "total_reviews": stats["total_reviews"],
            "badges": badges,
        }

    def _calculate_badges(self, stats: dict) -> list[str]:
        """
        Calculate tutor badges based on statistics.

        Badge criteria:
        - Popular Tutor: 10+ reviews AND 4.5+ avg rating
        - Best Tutor: 30+ reviews AND 4.8+ avg rating
        - Response King: 80%+ reply rate

        Args:
            stats: Tutor statistics dict

        Returns:
            List of badge names
        """
        badges = []

        if stats["total_reviews"] >= 10 and stats["average_rating"] >= 4.5:
            badges.append("Popular Tutor")  # 인기 튜터

        if stats["total_reviews"] >= 30 and stats["average_rating"] >= 4.8:
            badges.append("Best Tutor")  # 베스트 튜터

        if stats["reply_rate"] >= 80:
            badges.append("Response King")  # 답변왕

        return badges

    def _moderate_content(self, content: str) -> None:
        """
        Moderate review content.

        Filters:
        1. Profanity (basic Korean profanity list)
        2. Phone numbers
        3. Ad content (external links, contact info)

        Args:
            content: Content to moderate

        Raises:
            ValueError: If content violates rules
        """
        # Basic Korean profanity filter (expandable list)
        profanity_list = [
            "시발", "병신", "개새끼", "지랄", "미친", "씨발",
            "fuck", "shit", "bitch", "asshole",
        ]
        content_lower = content.lower()
        for word in profanity_list:
            if word in content_lower:
                raise ValueError("부적절한 언어가 포함되어 있습니다.")

        # Phone number filter (Korean formats)
        phone_pattern = r"(\d{2,3}[-.\s]?\d{3,4}[-.\s]?\d{4})|(\d{10,11})"
        if re.search(phone_pattern, content):
            raise ValueError("전화번호를 포함할 수 없습니다.")

        # External link filter
        url_pattern = r"(https?:\/\/[^\s]+)|(www\.[^\s]+)"
        if re.search(url_pattern, content):
            raise ValueError("외부 링크를 포함할 수 없습니다.")

        # Contact info filter
        contact_keywords = ["카카오", "인스타", "telegram", "연락", "문의"]
        for keyword in contact_keywords:
            if keyword in content:
                raise ValueError("연락처 정보를 포함할 수 없습니다.")
