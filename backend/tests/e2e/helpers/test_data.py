"""Helper module for test data setup and cleanup in E2E tests."""
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import UserRole, BookingStatus, SessionStatus, TutorApprovalStatus
from infrastructure.persistence.models import (
    UserModel,
    TutorProfileModel,
    StudentProfileModel,
    AvailableSlotModel,
    BookingModel,
    BookingSessionModel,
    PaymentModel,
    ReviewModel,
)


class TestDataFactory:
    """Factory class for creating test data in E2E tests."""

    def __init__(self, session: AsyncSession):
        """Initialize with a database session."""
        self.session = session

    async def create_user(
        self,
        email: str,
        name: str,
        role: UserRole,
        is_active: bool = True,
    ) -> UserModel:
        """Create a test user."""
        user = UserModel(
            email=email,
            name=name,
            hashed_password="hashed_password",
            role=role,
            is_active=is_active,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def create_tutor(
        self,
        email: str = "tutor@test.com",
        name: str = "Test Tutor",
        bio: str = "Test tutor bio",
        subjects: list[str] | None = None,
        hourly_rate: int = 50000,
        region: str = "Seoul",
        approval_status: TutorApprovalStatus = TutorApprovalStatus.APPROVED,
    ) -> tuple[UserModel, TutorProfileModel]:
        """Create a complete tutor profile.

        Returns:
            Tuple of (user, tutor_profile)
        """
        user = await self.create_user(email, name, UserRole.TUTOR)

        tutor = TutorProfileModel(
            user_id=user.id,
            bio=bio,
            subjects=subjects or ["Math", "English"],
            hourly_rate=hourly_rate,
            approval_status=approval_status,
            region=region,
        )
        self.session.add(tutor)
        await self.session.flush()
        await self.session.refresh(tutor)

        return user, tutor

    async def create_student(
        self,
        email: str = "student@test.com",
        name: str = "Test Student",
        grade: int = 10,
        school: str = "Test School",
    ) -> tuple[UserModel, StudentProfileModel]:
        """Create a complete student profile.

        Returns:
            Tuple of (user, student_profile)
        """
        user = await self.create_user(email, name, UserRole.STUDENT)

        student = StudentProfileModel(
            user_id=user.id,
            grade=grade,
            school=school,
        )
        self.session.add(student)
        await self.session.flush()
        await self.session.refresh(student)

        return user, student

    async def create_available_slot(
        self,
        tutor_id: int,
        day_of_week: int,
        start_time: str,
        end_time: str,
        is_active: bool = True,
    ) -> AvailableSlotModel:
        """Create an available slot for a tutor."""
        slot = AvailableSlotModel(
            tutor_id=tutor_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            is_active=is_active,
        )
        self.session.add(slot)
        await self.session.flush()
        await self.session.refresh(slot)
        return slot

    async def create_booking(
        self,
        tutor_id: int,
        student_id: int,
        total_sessions: int = 4,
        status: BookingStatus = BookingStatus.PENDING,
        notes: str = "Test booking",
        start_days_from_now: int = 1,
    ) -> BookingModel:
        """Create a booking with sessions."""
        booking = BookingModel(
            student_id=student_id,
            tutor_id=tutor_id,
            status=status,
            total_sessions=total_sessions,
            completed_sessions=0,
            notes=notes,
        )
        self.session.add(booking)
        await self.session.flush()

        # Create booking sessions
        for i in range(total_sessions):
            session_date = date.today() + timedelta(
                days=start_days_from_now + (i * 7)
            )
            session = BookingSessionModel(
                booking_id=booking.id,
                session_date=session_date,
                session_time="14:00",
                status=SessionStatus.SCHEDULED,
            )
            self.session.add(session)

        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def create_payment(
        self,
        booking_id: int,
        student_id: int,
        tutor_id: int,
        amount: Decimal = Decimal("200000.00"),
        fee_rate: Decimal = Decimal("0.05"),
        status: str = "PAID",
    ) -> PaymentModel:
        """Create a payment record."""
        fee_amount = amount * fee_rate
        net_amount = amount - fee_amount

        payment = PaymentModel(
            booking_id=booking_id,
            student_id=student_id,
            tutor_id=tutor_id,
            amount=amount,
            fee_rate=fee_rate,
            fee_amount=fee_amount,
            net_amount=net_amount,
            status=status,
            pg_payment_key=f"test_pg_key_{booking_id}",
        )
        self.session.add(payment)
        await self.session.flush()
        await self.session.refresh(payment)
        return payment

    async def create_review(
        self,
        booking_id: int,
        tutor_id: int,
        student_id: int,
        overall_rating: int = 5,
        content: str = "Great tutor!",
        is_anonymous: bool = True,
    ) -> ReviewModel:
        """Create a review."""
        review = ReviewModel(
            booking_id=booking_id,
            tutor_id=tutor_id,
            student_id=student_id,
            overall_rating=overall_rating,
            kindness_rating=overall_rating,
            preparation_rating=overall_rating,
            improvement_rating=overall_rating,
            punctuality_rating=overall_rating,
            content=content,
            is_anonymous=is_anonymous,
        )
        self.session.add(review)
        await self.session.flush()
        await self.session.refresh(review)
        return review

    async def create_complete_booking_flow(
        self,
        start_days_from_now: int = 1,
    ) -> dict:
        """Create a complete booking flow: tutor, student, booking, payment.

        Returns:
            Dictionary with all created entities
        """
        # Create tutor and student
        _, tutor = await self.create_tutor(
            email="flow_tutor@test.com",
            name="Flow Test Tutor"
        )
        _, student = await self.create_tutor(
            email="flow_student@test.com",
            name="Flow Test Student"
        )

        # Create available slot
        await self.create_available_slot(
            tutor_id=tutor.id,
            day_of_week=1,
            start_time="14:00",
            end_time="16:00",
        )

        # Create booking
        booking = await self.create_booking(
            tutor_id=tutor.id,
            student_id=student.id,
            total_sessions=4,
            status=BookingStatus.APPROVED,
            start_days_from_now=start_days_from_now,
        )

        # Create payment
        payment = await self.create_payment(
            booking_id=booking.id,
            student_id=student.id,
            tutor_id=tutor.id,
        )

        return {
            "tutor": tutor,
            "student": student,
            "booking": booking,
            "payment": payment,
        }

    async def cleanup_user_data(self, user_id: int):
        """Clean up all data associated with a user."""
        from sqlalchemy import delete, text, select

        # Delete reviews by student
        await self.session.execute(
            delete(ReviewModel).where(ReviewModel.student_id == user_id)
        )

        # Delete payments
        await self.session.execute(
            delete(PaymentModel).where(
                (PaymentModel.student_id == user_id) | (PaymentModel.tutor_id == user_id)
            )
        )

        # Delete booking sessions
        # First get booking IDs
        booking_ids_result = await self.session.execute(
            select(BookingModel.id).where(
                (BookingModel.student_id == user_id) | (BookingModel.tutor_id == user_id)
            )
        )
        booking_ids = [row[0] for row in booking_ids_result.fetchall()]

        if booking_ids:
            await self.session.execute(
                delete(BookingSessionModel).where(
                    BookingSessionModel.booking_id.in_(booking_ids)
                )
            )

        # Delete bookings
        await self.session.execute(
            delete(BookingModel).where(
                (BookingModel.student_id == user_id) | (BookingModel.tutor_id == user_id)
            )
        )

        # Delete available slots
        await self.session.execute(
            delete(AvailableSlotModel).where(AvailableSlotModel.tutor_id == user_id)
        )

        # Delete tutor/student profiles
        await self.session.execute(
            delete(TutorProfileModel).where(TutorProfileModel.user_id == user_id)
        )
        await self.session.execute(
            delete(StudentProfileModel).where(StudentProfileModel.user_id == user_id)
        )

        # Delete user
        await self.session.execute(
            delete(UserModel).where(UserModel.id == user_id)
        )

        await self.session.commit()
