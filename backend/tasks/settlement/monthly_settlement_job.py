"""Monthly settlement batch job.

Runs on the 1st of each month to calculate settlements for the previous month.
"""
from datetime import date, timedelta
from typing import Optional

from config import settings
from infrastructure.database import get_async_session
from tasks.jobs.base import BatchJobResult
from tasks.settlement.monthly_settlement_use_case import MonthlySettlementUseCase


async def monthly_settlement_job(year_month: Optional[str] = None) -> BatchJobResult:
    """
    Monthly settlement calculation job.

    Runs on the 1st of each month to calculate settlements for the previous month.
    Aggregates all completed sessions from the target month per tutor.

    Formula:
        total_amount = sum of session fees (from tutor's hourly_rate)
        platform_fee = total_amount * 0.05 (5%)
        pg_fee = total_amount * 0.03 (3%)
        net_amount = total_amount - platform_fee - pg_fee

    Args:
        year_month: Year-month string in format "YYYY-MM" (defaults to previous month)

    Returns:
        BatchJobResult with processing statistics
    """
    if not settings.BATCH_JOBS_ENABLED:
        return BatchJobResult(success=True, message="Batch jobs disabled")

    # Determine target month
    if year_month is None:
        # Default to previous month
        today = date.today()
        if today.month == 1:
            target_date = date(today.year - 1, 12, 1)
        else:
            target_date = date(today.year, today.month - 1, 1)
        year_month = target_date.strftime("%Y-%m")

    processed = 0
    failed = 0
    errors = []

    try:
        async for db in get_async_session():
            use_case = MonthlySettlementUseCase(db)
            result = await use_case.calculate_monthly_settlements(year_month)

            processed = result.get("processed", 0)
            failed = result.get("failed", 0)
            errors = result.get("errors", [])

            message = (
                f"Monthly settlement calculation completed for {year_month}. "
                f"Processed: {processed}, Failed: {failed}"
            )

            return BatchJobResult(
                success=failed == 0,
                processed_count=processed,
                failed_count=failed,
                errors=errors,
                message=message,
            )

    except Exception as e:
        return BatchJobResult(
            success=False,
            errors=[f"Job failed: {str(e)}"],
            message=f"Monthly settlement job failed: {str(e)}",
        )
