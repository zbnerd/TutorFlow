"""Settlement repository implementation."""
from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import select, and_, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Settlement, Money, SessionStatus, BookingStatus
from domain.ports import SettlementRepositoryPort
from infrastructure.persistence.models import (
    SettlementModel,
    BookingSessionModel,
    BookingModel,
    TutorModel,
)
from infrastructure.persistence.repositories.audit_log_repository import AuditLogRepository


class SettlementRepository(SettlementRepositoryPort):
    """SQLAlchemy implementation of SettlementRepositoryPort."""

    def __init__(self, session: AsyncSession, audit_repo: Optional[AuditLogRepository] = None):
        """Initialize repository with database session and optional audit repository."""
        self.session = session
        self.audit_repo = audit_repo

    async def save(
        self,
        settlement: Settlement,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Settlement:
        """Save settlement to database (create or update)."""
        if settlement.id is None:
            # Create new settlement
            new_values = {
                "tutor_id": settlement.tutor_id,
                "year_month": settlement.year_month,
                "total_sessions": settlement.total_sessions,
                "total_amount": settlement.total_amount.amount_krw if settlement.total_amount else 0,
                "platform_fee": settlement.platform_fee.amount_krw if settlement.platform_fee else 0,
                "net_amount": settlement.net_amount.amount_krw if settlement.net_amount else 0,
                "is_paid": settlement.is_paid,
            }
            db_settlement = SettlementModel(
                tutor_id=settlement.tutor_id,
                year_month=settlement.year_month,
                total_sessions=settlement.total_sessions,
                total_amount=settlement.total_amount.amount_krw if settlement.total_amount else 0,
                total_fee=settlement.platform_fee.amount_krw if settlement.platform_fee else 0,
                net_amount=settlement.net_amount.amount_krw if settlement.net_amount else 0,
                is_paid=settlement.is_paid,
                paid_at=settlement.paid_at,
            )
            self.session.add(db_settlement)
            await self.session.flush()
            await self.session.refresh(db_settlement)

            # Log creation
            if self.audit_repo:
                await self.audit_repo.log_change(
                    entity_type="settlement",
                    entity_id=db_settlement.id,
                    action="create",
                    old_value=None,
                    new_value=new_values,
                    actor_id=actor_id,
                    ip_address=ip_address,
                )

            return self._to_entity(db_settlement)
        else:
            # Update existing settlement
            result = await self.session.execute(
                select(SettlementModel).where(SettlementModel.id == settlement.id)
            )
            db_settlement = result.scalar_one_or_none()
            if db_settlement:
                # Capture old values for audit
                old_values = {
                    "total_sessions": db_settlement.total_sessions,
                    "total_amount": db_settlement.total_amount,
                    "total_fee": db_settlement.total_fee,
                    "net_amount": db_settlement.net_amount,
                    "is_paid": db_settlement.is_paid,
                    "paid_at": db_settlement.paid_at.isoformat() if db_settlement.paid_at else None,
                }

                db_settlement.total_sessions = settlement.total_sessions
                db_settlement.total_amount = settlement.total_amount.amount_krw if settlement.total_amount else 0
                db_settlement.total_fee = settlement.platform_fee.amount_krw if settlement.platform_fee else 0
                db_settlement.net_amount = settlement.net_amount.amount_krw if settlement.net_amount else 0
                db_settlement.is_paid = settlement.is_paid
                db_settlement.paid_at = settlement.paid_at
                await self.session.flush()
                await self.session.refresh(db_settlement)

                # Capture new values for audit
                new_values = {
                    "total_sessions": settlement.total_sessions,
                    "total_amount": settlement.total_amount.amount_krw if settlement.total_amount else 0,
                    "platform_fee": settlement.platform_fee.amount_krw if settlement.platform_fee else 0,
                    "net_amount": settlement.net_amount.amount_krw if settlement.net_amount else 0,
                    "is_paid": settlement.is_paid,
                    "paid_at": settlement.paid_at.isoformat() if settlement.paid_at else None,
                }

                # Log update if something changed
                if self.audit_repo and old_values != new_values:
                    await self.audit_repo.log_change(
                        entity_type="settlement",
                        entity_id=db_settlement.id,
                        action="update",
                        old_value=old_values,
                        new_value=new_values,
                        actor_id=actor_id,
                        ip_address=ip_address,
                    )

                return self._to_entity(db_settlement)
            return settlement

    async def find_by_id(self, settlement_id: int) -> Optional[Settlement]:
        """Find settlement by ID."""
        result = await self.session.execute(
            select(SettlementModel).where(SettlementModel.id == settlement_id)
        )
        db_settlement = result.scalar_one_or_none()
        return self._to_entity(db_settlement) if db_settlement else None

    async def get_monthly_settlements(
        self,
        tutor_id: int,
        year_month: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Settlement]:
        """Get monthly settlements for a tutor.

        Args:
            tutor_id: Tutor ID
            year_month: Optional year_month filter (e.g., "2024-01")
            offset: Pagination offset
            limit: Pagination limit

        Returns:
            List of settlements
        """
        query = select(SettlementModel).where(SettlementModel.tutor_id == tutor_id)
        if year_month:
            query = query.where(SettlementModel.year_month == year_month)
        query = query.order_by(SettlementModel.year_month.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        db_settlements = result.scalars().all()
        return [self._to_entity(s) for s in db_settlements]

    async def find_by_tutor_and_month(
        self,
        tutor_id: int,
        year_month: str,
    ) -> Optional[Settlement]:
        """Find settlement by tutor and year_month.

        Args:
            tutor_id: Tutor ID
            year_month: Year-month string (e.g., "2024-01")

        Returns:
            Settlement if found, None otherwise
        """
        result = await self.session.execute(
            select(SettlementModel).where(
                and_(
                    SettlementModel.tutor_id == tutor_id,
                    SettlementModel.year_month == year_month,
                )
            )
        )
        db_settlement = result.scalar_one_or_none()
        return self._to_entity(db_settlement) if db_settlement else None

    async def create_settlement(
        self,
        tutor_id: int,
        year_month: str,
        total_sessions: int,
        total_amount: Money,
        platform_fee: Money,
        pg_fee: Money,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Settlement:
        """Create a new settlement record.

        Args:
            tutor_id: Tutor ID
            year_month: Year-month string (e.g., "2024-01")
            total_sessions: Total number of sessions
            total_amount: Total amount before fees
            platform_fee: Platform fee amount
            pg_fee: Payment gateway fee amount

        Returns:
            Created settlement
        """
        settlement = Settlement(
            tutor_id=tutor_id,
            year_month=year_month,
            total_sessions=total_sessions,
            total_amount=total_amount,
            platform_fee=platform_fee,
            pg_fee=pg_fee,
            is_paid=False,
        )
        settlement.calculate_net_amount()
        return await self.save(settlement, actor_id, ip_address)

    async def mark_as_paid(
        self,
        settlement_id: int,
        paid_at: Optional[datetime] = None,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Settlement:
        """Mark settlement as paid.

        Args:
            settlement_id: Settlement ID
            paid_at: Optional payment timestamp (defaults to now)

        Returns:
            Updated settlement

        Raises:
            ValueError: If settlement not found
        """
        settlement = await self.find_by_id(settlement_id)
        if not settlement:
            raise ValueError(f"Settlement not found: {settlement_id}")

        old_is_paid = settlement.is_paid
        settlement.mark_as_paid(paid_at)

        # Log payment status change
        if self.audit_repo and not old_is_paid:
            await self.audit_repo.log_change(
                entity_type="settlement",
                entity_id=settlement_id,
                action="mark_paid",
                old_value={"is_paid": False, "paid_at": None},
                new_value={"is_paid": True, "paid_at": settlement.paid_at.isoformat() if settlement.paid_at else None},
                actor_id=actor_id,
                ip_address=ip_address,
            )

        return await self.save(settlement, actor_id, ip_address)

    async def list_pending_settlements(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Settlement]:
        """List all pending settlements (not yet paid).

        Args:
            offset: Pagination offset
            limit: Pagination limit

        Returns:
            List of pending settlements
        """
        query = select(SettlementModel).where(SettlementModel.is_paid == False)
        query = query.order_by(SettlementModel.year_month.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        db_settlements = result.scalars().all()
        return [self._to_entity(s) for s in db_settlements]

    async def get_tutor_revenue_for_month(
        self,
        month_start: date,
        month_end: date,
    ) -> dict[int, dict]:
        """Calculate revenue for each tutor from completed sessions in a month.

        Args:
            month_start: First day of the month
            month_end: Last day of the month

        Returns:
            Dictionary mapping tutor_id to revenue data:
            {
                tutor_id: {
                    "total_amount": int,  # Total amount in KRW
                    "total_sessions": int,  # Number of completed sessions
                }
            }
        """
        # Query completed sessions within the date range
        result = await self.session.execute(
            select(
                TutorModel.id,
                TutorModel.hourly_rate,
                sql_func.count(BookingSessionModel.id).label("session_count"),
            )
            .join(BookingModel, TutorModel.id == BookingModel.tutor_id)
            .join(BookingSessionModel, BookingModel.id == BookingSessionModel.booking_id)
            .where(
                and_(
                    BookingSessionModel.session_date >= month_start,
                    BookingSessionModel.session_date <= month_end,
                    BookingSessionModel.status == SessionStatus.COMPLETED,
                    BookingModel.status.in_(
                        [
                            BookingStatus.APPROVED,
                            BookingStatus.IN_PROGRESS,
                            BookingStatus.COMPLETED,
                        ]
                    ),
                )
            )
            .group_by(TutorModel.id, TutorModel.hourly_rate)
        )

        tutor_revenue = {}
        for row in result:
            tutor_id = row[0]
            hourly_rate = row[1]
            session_count = row[2]

            # Calculate total amount (hourly_rate * session_count)
            total_amount = (hourly_rate or 0) * session_count

            tutor_revenue[tutor_id] = {
                "total_amount": total_amount,
                "total_sessions": session_count,
            }

        return tutor_revenue

    def _to_entity(self, db_settlement: SettlementModel) -> Settlement:
        """Convert ORM model to domain entity."""
        return Settlement(
            id=db_settlement.id,
            tutor_id=db_settlement.tutor_id,
            year_month=db_settlement.year_month,
            total_sessions=db_settlement.total_sessions,
            total_amount=Money(db_settlement.total_amount) if db_settlement.total_amount else None,
            platform_fee=Money(db_settlement.total_fee) if db_settlement.total_fee else None,
            pg_fee=Money(0),  # Not stored separately in ORM, calculated from total_fee
            net_amount=Money(db_settlement.net_amount) if db_settlement.net_amount else None,
            is_paid=db_settlement.is_paid,
            paid_at=db_settlement.paid_at,
            created_at=db_settlement.created_at,
        )
