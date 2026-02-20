"""Repository factory for dependency injection."""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.persistence.repositories.attendance_repository import AttendanceRepository
from infrastructure.persistence.repositories.audit_log_repository import AuditLogRepository
from infrastructure.persistence.repositories.available_slot_repository import AvailableSlotRepository
from infrastructure.persistence.repositories.booking_repository import BookingRepository
from infrastructure.persistence.repositories.payment_repository import PaymentRepository
from infrastructure.persistence.repositories.review_repository import ReviewRepository
from infrastructure.persistence.repositories.settlement_repository import SettlementRepository
from infrastructure.persistence.repositories.tutor_repository import TutorRepository
from infrastructure.persistence.repositories.user_repository import UserRepository


class RepositoryFactory:
    """
    Factory for creating repository instances with database session injection.

    This provides a single point of dependency injection for all repositories,
    making it easier to manage dependencies and add cross-cutting concerns like
    audit logging.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository factory with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self._audit_repo: Optional[AuditLogRepository] = None

    def audit_log(self) -> AuditLogRepository:
        """Get or create audit log repository."""
        if self._audit_repo is None:
            self._audit_repo = AuditLogRepository(self.session)
        return self._audit_repo

    def user(self) -> UserRepository:
        """Get user repository with audit logging support."""
        return UserRepository(self.session, audit_repo=self.audit_log())

    def tutor(self) -> TutorRepository:
        """Get tutor repository with audit logging support."""
        return TutorRepository(self.session, audit_repo=self.audit_log())

    def student(self) -> TutorRepository:
        """
        Get student repository.

        Note: Students are managed through the User entity with STUDENT role.
        This is an alias for consistency in naming.
        """
        return TutorRepository(self.session, audit_repo=self.audit_log())

    def available_slot(self) -> AvailableSlotRepository:
        """Get available slot repository with audit logging support."""
        return AvailableSlotRepository(self.session, audit_repo=self.audit_log())

    def booking(self) -> BookingRepository:
        """Get booking repository with audit logging support."""
        return BookingRepository(self.session, audit_repo=self.audit_log())

    def payment(self) -> PaymentRepository:
        """Get payment repository with audit logging support."""
        return PaymentRepository(self.session, audit_repo=self.audit_log())

    def settlement(self) -> SettlementRepository:
        """Get settlement repository with audit logging support."""
        return SettlementRepository(self.session, audit_repo=self.audit_log())

    def review(self) -> ReviewRepository:
        """Get review repository with audit logging support."""
        return ReviewRepository(self.session, audit_repo=self.audit_log())

    def attendance(self) -> AttendanceRepository:
        """Get attendance repository with audit logging support."""
        return AttendanceRepository(self.session, audit_repo=self.audit_log())
