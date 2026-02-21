"""Monthly settlement use case."""
from datetime import date, timedelta

from domain.entities import Money
from domain.ports import SettlementRepositoryPort


class MonthlySettlementUseCase:
    """Use case for calculating monthly settlements."""

    def __init__(self, settlement_repo: SettlementRepositoryPort):
        """Initialize with settlement repository."""
        self.settlement_repo = settlement_repo
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
        tutor_revenue = await self.settlement_repo.get_tutor_revenue_for_month(
            month_start, month_end
        )

        for tutor_id, revenue_data in tutor_revenue.items():
            try:
                # Check if settlement already exists
                existing = await self.settlement_repo.find_by_tutor_and_month(
                    tutor_id, year_month
                )
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

                # Create settlement using repository
                await self.settlement_repo.create_settlement(
                    tutor_id=tutor_id,
                    year_month=year_month,
                    total_sessions=total_sessions,
                    total_amount=Money(amount_krw=total_amount),
                    platform_fee=Money(amount_krw=platform_fee_amount),
                    pg_fee=Money(amount_krw=pg_fee_amount),
                )

                processed += 1

            except Exception as e:
                failed += 1
                errors.append(f"Tutor {tutor_id}: {str(e)}")

        return {
            "processed": processed,
            "failed": failed,
            "errors": errors,
        }
