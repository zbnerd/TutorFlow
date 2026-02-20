"""Settlement use cases for monthly tutor payment calculations."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Settlement, Money
from domain.ports import SettlementRepositoryPort
from infrastructure.persistence.models import (
    SettlementModel,
    BookingSessionModel,
    BookingModel,
    TutorModel,
)


@dataclass
class CalculateSettlementUseCase:
    """
    Use case for calculating monthly tutor settlements.

    Business logic:
    - Aggregates completed sessions for a tutor in a given month
    - Calculates platform fee (5%) and PG fee (3%)
    - Returns net settlement amount
    """

    settlement_repo: SettlementRepositoryPort
    PLATFORM_FEE_RATE = 0.05  # 5%
    PG_FEE_RATE = 0.03  # 3%

    async def calculate_monthly_settlement(
        self,
        tutor_id: int,
        year_month: str,
        db: AsyncSession,
    ) -> Settlement:
        """
        Calculate monthly settlement for a tutor.

        Args:
            tutor_id: Tutor ID
            year_month: Year-month string in format "YYYY-MM"
            db: Database session for queries

        Returns:
            Settlement entity with calculated amounts

        Raises:
            ValueError: If validation fails
        """
        # Parse year_month to get date range
        year, month = map(int, year_month.split("-"))
        month_start = date(year, month, 1)

        # Calculate month end
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)

        # Calculate tutor revenue for the month
        tutor_revenue = await self._calculate_tutor_revenue(db, month_start, month_end)

        if tutor_id not in tutor_revenue:
            raise ValueError(f"No completed sessions found for tutor {tutor_id} in {year_month}")

        revenue_data = tutor_revenue[tutor_id]
        total_amount = revenue_data["total_amount"]
        total_sessions = revenue_data["total_sessions"]

        # Calculate fees
        platform_fee_amount = int(total_amount * self.PLATFORM_FEE_RATE)
        pg_fee_amount = int(total_amount * self.PG_FEE_RATE)
        net_amount = total_amount - platform_fee_amount - pg_fee_amount

        # Create settlement entity
        settlement = Settlement(
            tutor_id=tutor_id,
            year_month=year_month,
            total_sessions=total_sessions,
            total_amount=Money(amount_krw=total_amount, currency="KRW"),
            platform_fee=Money(amount_krw=platform_fee_amount, currency="KRW"),
            pg_fee=Money(amount_krw=pg_fee_amount, currency="KRW"),
            net_amount=Money(amount_krw=net_amount, currency="KRW"),
            is_paid=False,
            paid_at=None,
            created_at=datetime.utcnow(),
        )

        return await self.settlement_repo.save(settlement)

    async def _calculate_tutor_revenue(
        self,
        db: AsyncSession,
        month_start: date,
        month_end: date,
    ) -> dict[int, dict]:
        """
        Calculate revenue for each tutor from completed sessions in a month.

        Args:
            db: Database session
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
        result = await db.execute(
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
                    BookingSessionModel.status == "completed",
                    BookingModel.status.in_([
                        "approved",
                        "in_progress",
                        "completed",
                    ]),
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

    async def calculate_all_tutors_settlement(
        self,
        year_month: str,
        db: AsyncSession,
    ) -> dict[str, int]:
        """
        Calculate settlements for all tutors in a given month.

        Args:
            year_month: Year-month string in format "YYYY-MM"
            db: Database session

        Returns:
            Dictionary with "processed" and "failed" counts
        """
        # Parse year_month to get date range
        year, month = map(int, year_month.split("-"))
        month_start = date(year, month, 1)

        # Calculate month end
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)

        # Get all tutors with completed sessions
        tutor_revenue = await self._calculate_tutor_revenue(db, month_start, month_end)

        processed = 0
        failed = 0

        for tutor_id in tutor_revenue.keys():
            try:
                # Check if settlement already exists
                existing = await self._get_existing_settlement(db, tutor_id, year_month)
                if existing:
                    failed += 1
                    continue

                await self.calculate_monthly_settlement(tutor_id, year_month, db)
                processed += 1
            except Exception:
                failed += 1

        return {"processed": processed, "failed": failed}

    async def _get_existing_settlement(
        self,
        db: AsyncSession,
        tutor_id: int,
        year_month: str,
    ) -> Optional[SettlementModel]:
        """
        Check if a settlement already exists for the tutor and month.

        Args:
            db: Database session
            tutor_id: Tutor ID
            year_month: Year-month string

        Returns:
            Existing settlement or None
        """
        result = await db.execute(
            select(SettlementModel).where(
                and_(
                    SettlementModel.tutor_id == tutor_id,
                    SettlementModel.year_month == year_month,
                )
            )
        )
        return result.scalar_one_or_none()
