"""Repository implementations for domain entities."""
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import User, Review, ReviewReport, Booking, Payment
from domain.ports import UserRepositoryPort, ReviewRepositoryPort, PaymentRepositoryPort, BookingRepositoryPort
from infrastructure.persistence.models import UserModel, ReviewModel, ReviewReportModel, BookingModel, PaymentModel


class UserRepository(UserRepositoryPort):
    """SQLAlchemy implementation of UserRepositoryPort."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def save(self, user: User) -> User:
        """Save user to database (create or update)."""
        if user.id is None:
            # Create new user
            db_user = UserModel.from_entity(user)
            self.session.add(db_user)
            await self.session.flush()
            await self.session.refresh(db_user)
            return db_user.to_entity()
        else:
            # Update existing user
            result = await self.session.execute(select(UserModel).where(UserModel.id == user.id))
            db_user = result.scalar_one_or_none()
            if db_user:
                db_user.email = user.email
                db_user.name = user.name
                db_user.phone = user.phone
                db_user.role = user.role
                db_user.profile_image_url = user.profile_image_url
                db_user.is_active = user.is_active
                db_user.is_verified = user.is_verified
                await self.session.flush()
                await self.session.refresh(db_user)
                return db_user.to_entity()
            return user

    async def find_by_id(self, user_id: int) -> Optional[User]:
        """Find user by ID."""
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        db_user = result.scalar_one_or_none()
        return db_user.to_entity() if db_user else None

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        result = await self.session.execute(select(UserModel).where(UserModel.email == email))
        db_user = result.scalar_one_or_none()
        return db_user.to_entity() if db_user else None

    async def find_by_oauth_id(self, provider: str, oauth_id: str) -> Optional[User]:
        """Find user by OAuth provider ID."""
        result = await self.session.execute(
            select(UserModel).where(
                UserModel.oauth_provider == provider,
                UserModel.oauth_id == oauth_id,
            )
        )
        db_user = result.scalar_one_or_none()
        return db_user.to_entity() if db_user else None


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
            )
            self.session.add(db_review)
            await self.session.flush()
            await self.session.refresh(db_review)
            return self._to_entity(db_review)
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
                return self._to_entity(db_review)
            return review

    async def find_by_id(self, review_id: int) -> Optional[Review]:
        """Find review by ID."""
        result = await self.session.execute(
            select(ReviewModel).where(ReviewModel.id == review_id)
        )
        db_review = result.scalar_one_or_none()
        return self._to_entity(db_review) if db_review else None

    async def list_by_tutor(
        self,
        tutor_id: int,
        min_rating: float | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Review]:
        """List reviews for a tutor."""
        query = select(ReviewModel).where(ReviewModel.tutor_id == tutor_id)

        if min_rating is not None:
            query = query.where(ReviewModel.overall_rating >= min_rating)

        query = query.order_by(ReviewModel.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        db_reviews = result.scalars().all()
        return [self._to_entity(r) for r in db_reviews]

    async def find_by_booking_id(self, booking_id: int) -> Optional[Review]:
        """Find review by booking ID (one review per booking)."""
        result = await self.session.execute(
            select(ReviewModel).where(ReviewModel.booking_id == booking_id)
        )
        db_review = result.scalar_one_or_none()
        return self._to_entity(db_review) if db_review else None

    async def can_create_review(self, booking_id: int) -> tuple[bool, str]:
        """
        Check if user can create a review for this booking.

        Requirements:
        1. Payment status must be PAID
        2. At least 1 completed session
        3. No existing review for this booking

        Returns:
            Tuple of (can_create: bool, reason: str)
        """
        # Check if review already exists
        existing_review = await self.find_by_booking_id(booking_id)
        if existing_review:
            return False, "이미 리뷰를 작성했습니다."

        # Check booking and payment status
        result = await self.session.execute(
            select(BookingModel, PaymentModel)
            .join(PaymentModel, BookingModel.id == PaymentModel.booking_id)
            .where(BookingModel.id == booking_id)
        )
        row = result.first()
        if not row:
            return False, "예약을 찾을 수 없습니다."

        booking, payment = row

        # Check payment status
        if payment.status != "paid":
            return False, "결제가 완료되지 않은 예약입니다."

        # Check completed sessions
        if booking.completed_sessions < 1:
            return False, "최소 1회 이상 수업이 완료된 예약만 리뷰를 작성할 수 있습니다."

        return True, ""

    async def get_tutor_stats(self, tutor_id: int) -> dict:
        """
        Get tutor review statistics for badge calculation.

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

    def _to_entity(self, db_review: ReviewModel) -> Review:
        """Convert ORM model to domain entity."""
        return Review(
            id=db_review.id,
            booking_id=db_review.booking_id,
            tutor_id=db_review.tutor_id,
            student_id=db_review.student_id,
            overall_rating=db_review.overall_rating,
            kindness_rating=db_review.kindness_rating,
            preparation_rating=db_review.preparation_rating,
            improvement_rating=db_review.improvement_rating,
            punctuality_rating=db_review.punctuality_rating,
            content=db_review.content,
            is_anonymous=db_review.is_anonymous,
            tutor_reply=db_review.tutor_reply,
            tutor_replied_at=db_review.tutor_replied_at,
            created_at=db_review.created_at,
            updated_at=db_review.updated_at,
        )


class ReviewReportRepository:
    """Repository for review reports."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def save(self, report: ReviewReport) -> ReviewReport:
        """Save review report to database."""
        db_report = ReviewReportModel(
            review_id=report.review_id,
            reporter_id=report.reporter_id,
            reason=report.reason,
            description=report.description,
            is_processed=report.is_processed,
            processed_by=report.processed_by,
            processed_at=report.processed_at,
        )
        self.session.add(db_report)
        await self.session.flush()
        await self.session.refresh(db_report)

        return ReviewReport(
            id=db_report.id,
            review_id=db_report.review_id,
            reporter_id=db_report.reporter_id,
            reason=db_report.reason,
            description=db_report.description,
            is_processed=db_report.is_processed,
            processed_by=db_report.processed_by,
            processed_at=db_report.processed_at,
            created_at=db_report.created_at,
        )
