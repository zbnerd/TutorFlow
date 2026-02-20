"""Monthly settlement use case."""
from datetime import date, timedelta, datetime
from typing import Optional

from sqlalchemy import select, and_, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from infrastructure.persistence.models import (
    SettlementModel,
    BookingSessionModel,
    BookingModel,
    TutorModel,
)


class MonthlySettlementUseCase:
    """Use case for calculating monthly settlements."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self.platform_fee_rate = 0.05  # 5%
        self.pg_fee_rate = 0.03  # 3%

    async def calculate_monthly_settlements(self, year_month: str) -> dict:
        """
        Calculate monthly settlements for all tutors.

        Args:
            year_month: Year-month string in format "YYYY-MM"

        Returns:
            Dict with processed, failed, errors keys
        """
        # Parse year_month to get date range
        year, month = map(int, year_month.split("-"))
        month_start = date(year, month, 1)

        # Calculate month end
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)

        processed = 0
        failed = 0
        errors = []

        # Get all tutors who have completed sessions in the target month
        tutor_revenue = await self._calculate_tutor_revenue(month_start, month_end)

        for tutor_id, revenue_data in tutor_revenue.items():
            try:
                # Check if settlement already exists
                existing = await self._get_existing_settlement(tutor_id, year_month)
                if existing:
                    errors.append(
                        f"Tutor {tutor_id}: Settlement for {year_month} already exists (ID: {existing.id})"
                    )
                    failed += 1
                    continue

                # Calculate settlement amounts
                total_amount = revenue_data["total_amount"]
                total_sessions = revenue_data["total_sessions"]

                # Calculate fees
                platform_fee_amount = int(total_amount * self.platform_fee_rate)
                pg_fee_amount = int(total_amount * self.pg_fee_rate)
                net_amount = total_amount - platform_fee_amount - pg_fee_amount

                # Create settlement record
                settlement = SettlementModel(
                    tutor_id=tutor_id,
                    year_month=year_month,
                    total_sessions=total_sessions,
                    total_amount=total_amount,
                    total_fee=platform_fee_amount + pg_fee_amount,
                    net_amount=net_amount,
                    is_paid=False,
                    paid_at=None,
                    created_at=datetime.utcnow(),
                )

                self.db.add(settlement)
                await self.db.flush()

                processed += 1

            except Exception as e:
                failed += 1
                errors.append(f"Tutor {tutor_id}: {str(e)}")

        # Commit all settlements
        await self.db.commit()

        return {
            "processed": processed,
            "failed": failed,
            "errors": errors,
        }

    async def _calculate_tutor_revenue(
        self,
        month_start: date,
        month_end: date,
    ) -> dict[int, dict]:
        """Calculate revenue for each tutor from completed sessions in a month."""
        from domain.entities import SessionStatus, BookingStatus

        # Query completed sessions within the date range
        result = await self.db.execute(
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
                    BookingModel.status.in_([
                        BookingStatus.APPROVED,
                        BookingStatus.IN_PROGRESS,
                        BookingStatus.COMPLETED,
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

    async def _get_existing_settlement(
        self,
        tutor_id: int,
        year_month: str,
    ) -> Optional[SettlementModel]:
        """Check if a settlement already exists for the tutor and month."""
        result = await self.db.execute(
            select(SettlementModel).where(
                and_(
                    SettlementModel.tutor_id == tutor_id,
                    SettlementModel.year_month == year_month,
                )
            )
        )
        return result.scalar_one_or_none()
