"""Port interfaces for external dependencies (Protocol definitions)."""

from typing import Protocol, runtime_checkable

from domain.entities import User, Tutor, Student, Booking, Payment, Review


@runtime_checkable
class PaymentPort(Protocol):
    """Payment gateway interface."""

    async def create_payment(
        self,
        amount: int,
        booking_id: int,
        user_id: int,
        order_name: str,
    ) -> dict:
        """Create a payment request and return payment details."""

    async def verify_payment(self, payment_key: str, amount: int) -> dict:
        """Verify payment status and details."""

    async def cancel_payment(self, payment_key: str, cancel_reason: str) -> dict:
        """Cancel a payment."""


@runtime_checkable
class NotificationPort(Protocol):
    """Notification service interface."""

    async def send_sms(self, phone: str, message: str) -> bool:
        """Send SMS notification."""

    async def send_alimtalk(
        self,
        phone: str,
        template_code: str,
        variables: dict,
    ) -> bool:
        """Send Kakao Alimtalk notification."""


@runtime_checkable
class OAuthPort(Protocol):
    """OAuth provider interface."""

    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for access token."""

    async def get_user_info(self, access_token: str) -> dict:
        """Get user information from OAuth provider."""


@runtime_checkable
class UserRepositoryPort(Protocol):
    """User repository interface."""

    async def save(self, user: User) -> User:
        """Save user to database."""

    async def find_by_id(self, user_id: int) -> User | None:
        """Find user by ID."""

    async def find_by_email(self, email: str) -> User | None:
        """Find user by email."""

    async def find_by_oauth_id(self, provider: str, oauth_id: str) -> User | None:
        """Find user by OAuth provider ID."""


@runtime_checkable
class TutorRepositoryPort(Protocol):
    """Tutor repository interface."""

    async def save(self, tutor: Tutor) -> Tutor:
        """Save tutor to database."""

    async def find_by_id(self, tutor_id: int) -> Tutor | None:
        """Find tutor by ID."""

    async def find_by_user_id(self, user_id: int) -> Tutor | None:
        """Find tutor profile by user ID."""

    async def list_approved(
        self,
        offset: int = 0,
        limit: int = 20,
        subject: str | None = None,
    ) -> list[Tutor]:
        """List approved tutors with optional filtering."""


@runtime_checkable
class BookingRepositoryPort(Protocol):
    """Booking repository interface."""

    async def save(self, booking: Booking) -> Booking:
        """Save booking to database."""

    async def find_by_id(self, booking_id: int) -> Booking | None:
        """Find booking by ID."""

    async def list_by_tutor(
        self,
        tutor_id: int,
        status: str | None = None,
    ) -> list[Booking]:
        """List bookings by tutor."""

    async def list_by_student(
        self,
        student_id: int,
        status: str | None = None,
    ) -> list[Booking]:
        """List bookings by student."""


@runtime_checkable
class PaymentRepositoryPort(Protocol):
    """Payment repository interface."""

    async def save(self, payment: Payment) -> Payment:
        """Save payment to database."""

    async def find_by_id(self, payment_id: int) -> Payment | None:
        """Find payment by ID."""

    async def find_by_booking_id(self, booking_id: int) -> Payment | None:
        """Find payment by booking ID."""

    async def find_by_pg_key(self, pg_payment_key: str) -> Payment | None:
        """Find payment by payment gateway key."""


@runtime_checkable
class ReviewRepositoryPort(Protocol):
    """Review repository interface."""

    async def save(self, review: Review) -> Review:
        """Save review to database."""

    async def find_by_id(self, review_id: int) -> Review | None:
        """Find review by ID."""

    async def list_by_tutor(
        self,
        tutor_id: int,
        min_rating: float | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Review]:
        """List reviews for a tutor."""

    async def find_by_booking_id(self, booking_id: int) -> Review | None:
        """Find review by booking ID (one review per booking)."""


@runtime_checkable
class TokenPort(Protocol):
    """JWT token service interface."""

    def create_access_token(self, data: dict) -> str:
        """Create JWT access token."""

    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token."""

    def decode_token(self, token: str) -> dict:
        """Decode and verify JWT token."""
