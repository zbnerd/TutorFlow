"""Settlement repository implementation."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Settlement, Money
from domain.ports import SettlementRepositoryPort
from infrastructure.persistence.models import SettlementModel


class SettlementRepository(SettlementRepositoryPort):
    """SQLAlchemy implementation of SettlementRepositoryPort."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def save(self, settlement: Settlement) -> Settlement:
        """Save settlement to database (create or update)."""
        if settlement.id is None:
            # Create new settlement
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
            return self._to_entity(db_settlement)
        else:
            # Update existing settlement
            result = await self.session.execute(
                select(SettlementModel).where(SettlementModel.id == settlement.id)
            )
            db_settlement = result.scalar_one_or_none()
            if db_settlement:
                db_settlement.total_sessions = settlement.total_sessions
                db_settlement.total_amount = settlement.total_amount.amount_krw if settlement.total_amount else 0
                db_settlement.total_fee = settlement.platform_fee.amount_krw if settlement.platform_fee else 0
                db_settlement.net_amount = settlement.net_amount.amount_krw if settlement.net_amount else 0
                db_settlement.is_paid = settlement.is_paid
                db_settlement.paid_at = settlement.paid_at
                await self.session.flush()
                await self.session.refresh(db_settlement)
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
        return await self.save(settlement)

    async def mark_as_paid(
        self,
        settlement_id: int,
        paid_at: Optional[datetime] = None,
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

        settlement.mark_as_paid(paid_at)
        return await self.save(settlement)

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
