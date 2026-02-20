"""E2E test configuration and fixtures.

This module provides shared fixtures for end-to-end testing of the TutorFlow API.
Since Playwright is not yet installed, these fixtures use httpx for async API testing.
"""
import asyncio
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from infrastructure.database import Base, get_db
from domain.entities import UserRole, BookingStatus, SessionStatus, TutorApprovalStatus
from infrastructure.external.auth import TokenService


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def e2e_engine():
    """Create test database engine for E2E tests."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def e2e_session(e2e_engine):
    """Create test database session for E2E tests."""
    async_session = async_sessionmaker(e2e_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def e2e_client(e2e_session):
    """Create test client with database override for E2E tests."""
    async def override_get_db():
        yield e2e_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def test_tutor(e2e_session):
    """Create a test tutor user."""
    from infrastructure.persistence.models import UserModel, TutorProfileModel
    from domain.value_objects.money import Money

    async with e2e_session.begin():
        # Create user
        user = UserModel(
            email="tutor@example.com",
            name="Test Tutor",
            hashed_password="hashed",
            role=UserRole.TUTOR,
            is_active=True,
        )
        e2e_session.add(user)
        await e2e_session.flush()

        # Create tutor profile
        tutor = TutorProfileModel(
            user_id=user.id,
            bio="Test tutor bio",
            subjects=["Math", "Science"],
            hourly_rate=50000,
            approval_status=TutorApprovalStatus.APPROVED,
            region="Seoul",
        )
        e2e_session.add(tutor)
        await e2e_session.commit()

        # Refresh to get ID
        await e2e_session.refresh(user)
        await e2e_session.refresh(tutor)

        return {"user_id": user.id, "tutor_id": tutor.id, "email": user.email}


@pytest.fixture
async def test_student(e2e_session):
    """Create a test student user."""
    from infrastructure.persistence.models import UserModel, StudentProfileModel

    async with e2e_session.begin():
        # Create user
        user = UserModel(
            email="student@example.com",
            name="Test Student",
            hashed_password="hashed",
            role=UserRole.STUDENT,
            is_active=True,
        )
        e2e_session.add(user)
        await e2e_session.flush()

        # Create student profile
        student = StudentProfileModel(
            user_id=user.id,
            grade=10,
            school="Test School",
        )
        e2e_session.add(student)
        await e2e_session.commit()

        # Refresh to get ID
        await e2e_session.refresh(user)
        await e2e_session.refresh(student)

        return {"user_id": user.id, "student_id": student.id, "email": user.email}


@pytest.fixture
def auth_headers(test_tutor):
    """Generate auth headers for test user."""
    token_service = TokenService()
    access_token = token_service.create_access_token(test_tutor["user_id"])
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def test_available_slot(e2e_session, test_tutor):
    """Create a test available slot for tutor."""
    from infrastructure.persistence.models import AvailableSlotModel

    async with e2e_session.begin():
        slot = AvailableSlotModel(
            tutor_id=test_tutor["tutor_id"],
            day_of_week=1,  # Monday
            start_time="14:00",
            end_time="16:00",
            is_active=True,
        )
        e2e_session.add(slot)
        await e2e_session.commit()
        await e2e_session.refresh(slot)
        return slot.id


@pytest.fixture
async def test_booking(e2e_session, test_tutor, test_student):
    """Create a test booking."""
    from infrastructure.persistence.models import BookingModel, BookingSessionModel
    from datetime import date, time

    async with e2e_session.begin():
        # Create booking
        booking = BookingModel(
            student_id=test_student["user_id"],
            tutor_id=test_tutor["tutor_id"],
            status=BookingStatus.PENDING,
            total_sessions=4,
            completed_sessions=0,
            notes="Test booking",
        )
        e2e_session.add(booking)
        await e2e_session.flush()

        # Create booking sessions (starting tomorrow)
        tomorrow = date.today() + timedelta(days=1)
        for i in range(4):
            session_date = tomorrow + timedelta(weeks=i)
            session = BookingSessionModel(
                booking_id=booking.id,
                session_date=session_date,
                session_time="14:00",
                status=SessionStatus.SCHEDULED,
            )
            e2e_session.add(session)

        await e2e_session.commit()
        await e2e_session.refresh(booking)

        return booking.id


@pytest.fixture
async def test_payment(e2e_session, test_tutor, test_student, test_booking):
    """Create a test payment record."""
    from infrastructure.persistence.models import PaymentModel
    from decimal import Decimal

    async with e2e_session.begin():
        payment = PaymentModel(
            booking_id=test_booking,
            student_id=test_student["user_id"],
            tutor_id=test_tutor["tutor_id"],
            amount=Decimal("200000.00"),
            fee_rate=Decimal("0.05"),
            fee_amount=Decimal("10000.00"),
            net_amount=Decimal("190000.00"),
            status="PAID",
            pg_payment_key="test_pg_key_123",
        )
        e2e_session.add(payment)
        await e2e_session.commit()
        await e2e_session.refresh(payment)
        return payment.id
