"""Review repository implementation."""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Review, ReviewReport
from domain.ports import ReviewRepositoryPort
from infrastructure.persistence.models import ReviewModel, ReviewReportModel


class ReviewRepository(ReviewRepositoryPort):
    """SQLAlchemy implementation of ReviewRepositoryPort."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def save(self, review: Review) -> Review:
        """Save review to database (create or update)."""
        if review.id is None:
            # Create new review
            db_review = ReviewModel(
                booking_id=review.booking_id,
                tutor_id=review.tutor_id,
                student_id=review.student_id,
                overall_rating=review.overall_rating,
                kindness_rating=review.kindness_rating,
                preparation_rating=review.preparation_rating,
                improvement_rating=review.improvement_rating,
                punctuality_rating=review.punctuality_rating,
                content=review.content,
                is_anonymous=review.is_anonymous,
                tutor_reply=review.tutor_reply,
                tutor_replied_at=review.tutor_replied_at,
                created_at=review.created_at or datetime.utcnow(),
            )
            self.session.add(db_review)
            await self.session.flush()
            await self.session.refresh(db_review)
            return db_review.to_entity()
        else:
            # Update existing review
            result = await self.session.execute(
                select(ReviewModel).where(ReviewModel.id == review.id)
            )
            db_review = result.scalar_one_or_none()
            if db_review:
                db_review.overall_rating = review.overall_rating
                db_review.kindness_rating = review.kindness_rating
                db_review.preparation_rating = review.preparation_rating
                db_review.improvement_rating = review.improvement_rating
                db_review.punctuality_rating = review.punctuality_rating
                db_review.content = review.content
                db_review.is_anonymous = review.is_anonymous
                db_review.tutor_reply = review.tutor_reply
                db_review.tutor_replied_at = review.tutor_replied_at
                await self.session.flush()
                await self.session.refresh(db_review)
                return db_review.to_entity()
            return review

    async def find_by_id(self, review_id: int) -> Optional[Review]:
        """Find review by ID."""
        result = await self.session.execute(
            select(ReviewModel).where(ReviewModel.id == review_id)
        )
        db_review = result.scalar_one_or_none()
        return db_review.to_entity() if db_review else None

    async def list_by_tutor(
        self,
        tutor_id: int,
        min_rating: Optional[float] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Review]:
        """List reviews for a tutor with optional rating filter."""
        query = select(ReviewModel).where(ReviewModel.tutor_id == tutor_id)

        if min_rating is not None:
            query = query.where(ReviewModel.overall_rating >= int(min_rating))

        query = query.order_by(ReviewModel.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        db_reviews = result.scalars().all()
        return [r.to_entity() for r in db_reviews]

    async def find_by_booking_id(self, booking_id: int) -> Optional[Review]:
        """Find review by booking ID (one review per booking)."""
        result = await self.session.execute(
            select(ReviewModel).where(ReviewModel.booking_id == booking_id)
        )
        db_review = result.scalar_one_or_none()
        return db_review.to_entity() if db_review else None

    async def get_tutor_stats(self, tutor_id: int) -> dict:
        """Get tutor review statistics for badge calculation."""
        # Count total reviews
        count_result = await self.session.execute(
            select(func.count(ReviewModel.id)).where(ReviewModel.tutor_id == tutor_id)
        )
        total_reviews = count_result.scalar() or 0

        if total_reviews == 0:
            return {
                "total_reviews": 0,
                "average_rating": 0.0,
                "reply_rate": 0.0,
            }

        # Calculate average rating
        avg_result = await self.session.execute(
            select(func.avg(ReviewModel.overall_rating)).where(
                ReviewModel.tutor_id == tutor_id
            )
        )
        average_rating = round(float(avg_result.scalar() or 0), 2)

        # Calculate reply rate (replies within 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        replies_result = await self.session.execute(
            select(func.count(ReviewModel.id)).where(
                and_(
                    ReviewModel.tutor_id == tutor_id,
                    ReviewModel.tutor_reply.isnot(None),
                    ReviewModel.tutor_replied_at >= week_ago,
                )
            )
        )
        recent_replies = replies_result.scalar() or 0

        reply_rate = round((recent_replies / total_reviews) * 100, 2) if total_reviews > 0 else 0.0

        return {
            "total_reviews": total_reviews,
            "average_rating": average_rating,
            "reply_rate": reply_rate,
        }

    async def delete(self, review_id: int) -> bool:
        """Delete review by ID."""
        result = await self.session.execute(
            select(ReviewModel).where(ReviewModel.id == review_id)
        )
        db_review = result.scalar_one_or_none()
        if db_review:
            await self.session.delete(db_review)
            await self.session.flush()
            return True
        return False

    async def add_tutor_reply(
        self, review_id: int, reply: str, replied_at: datetime
    ) -> Optional[Review]:
        """Add tutor reply to review."""
        result = await self.session.execute(
            select(ReviewModel).where(ReviewModel.id == review_id)
        )
        db_review = result.scalar_one_or_none()
        if db_review:
            db_review.tutor_reply = reply
            db_review.tutor_replied_at = replied_at
            await self.session.flush()
            await self.session.refresh(db_review)
            return db_review.to_entity()
        return None

    async def save_report(self, report: ReviewReport) -> ReviewReport:
        """Save review report to database."""
        if report.id is None:
            db_report = ReviewReportModel(
                review_id=report.review_id,
                reporter_id=report.reporter_id,
                reason=report.reason,
                description=report.description,
                is_processed=report.is_processed,
                processed_by=report.processed_by,
                processed_at=report.processed_at,
                created_at=report.created_at or datetime.utcnow(),
            )
            self.session.add(db_report)
            await self.session.flush()
            await self.session.refresh(db_report)
            return db_report.to_entity()
        else:
            result = await self.session.execute(
                select(ReviewReportModel).where(ReviewReportModel.id == report.id)
            )
            db_report = result.scalar_one_or_none()
            if db_report:
                db_report.is_processed = report.is_processed
                db_report.processed_by = report.processed_by
                db_report.processed_at = report.processed_at
                await self.session.flush()
                await self.session.refresh(db_report)
                return db_report.to_entity()
            return report

    async def find_report_by_id(self, report_id: int) -> Optional[ReviewReport]:
        """Find review report by ID."""
        result = await self.session.execute(
            select(ReviewReportModel).where(ReviewReportModel.id == report_id)
        )
        db_report = result.scalar_one_or_none()
        return db_report.to_entity() if db_report else None

    async def list_reports(
        self, is_processed: bool | None = None, offset: int = 0, limit: int = 20
    ) -> list[ReviewReport]:
        """List review reports with optional processing filter."""
        query = select(ReviewReportModel)

        if is_processed is not None:
            query = query.where(ReviewReportModel.is_processed == is_processed)

        query = query.order_by(ReviewReportModel.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        db_reports = result.scalars().all()
        return [r.to_entity() for r in db_reports]

    async def can_create_review(self, booking_id: int, student_id: int) -> tuple[bool, str, int | None]:
        """
        Check if student can create review for booking.

        Returns:
            Tuple of (can_create, error_message, tutor_id)
        """
        from infrastructure.persistence.models import BookingModel, PaymentModel

        # Check if booking exists and belongs to student
        booking_result = await self.session.execute(
            select(BookingModel).where(
                and_(BookingModel.id == booking_id, BookingModel.student_id == student_id)
            )
        )
        booking = booking_result.scalar_one_or_none()

        if not booking:
            return False, "예약을 찾을 수 없습니다.", None

        # Check if review already exists
        existing_review = await self.find_by_booking_id(booking_id)
        if existing_review:
            return False, "이미 리뷰를 작성했습니다.", None

        # Check payment status
        payment_result = await self.session.execute(
            select(PaymentModel).where(PaymentModel.booking_id == booking_id)
        )
        payment = payment_result.scalar_one_or_none()

        if not payment or payment.status.value != "paid":
            return False, "결제가 완료된 예약에만 리뷰를 작성할 수 있습니다.", None

        # Check if at least one session completed
        if booking.completed_sessions < 1:
            return False, "최소 1회 이상 수업이 완료된 후 리뷰를 작성할 수 있습니다.", None

        return True, "", booking.tutor_id

    async def is_review_editable(self, review_id: int, student_id: int) -> bool:
        """Check if review is editable (within 7 days of creation)."""
        result = await self.session.execute(
            select(ReviewModel).where(
                and_(ReviewModel.id == review_id, ReviewModel.student_id == student_id)
            )
        )
        db_review = result.scalar_one_or_none()

        if not db_review:
            return False

        # Allow editing within 7 days of creation
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        return db_review.created_at >= seven_days_ago
