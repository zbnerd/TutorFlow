"""Monthly settlement batch jobs for TutorFlow.

This module provides scheduled jobs for calculating and processing
monthly tutor settlements.

Jobs can be scheduled using Celery Beat, APScheduler, or any cron-compatible scheduler.
Runs on the 1st of each month to calculate settlements for the previous month.
"""
import asyncio
from datetime import date
from typing import Optional

from config import settings
from application.use_cases.settlement import CalculateSettlementUseCase
from domain.ports import SettlementRepositoryPort
from infrastructure.database import get_async_session
from infrastructure.persistence.repositories.settlement_repository import SettlementRepository


class BatchJobResult:
    """Result of a batch job execution."""

    def __init__(
        self,
        success: bool,
        processed_count: int = 0,
        failed_count: int = 0,
        errors: list[str] | None = None,
        message: str = "",
    ):
        self.success = success
        self.processed_count = processed_count
        self.failed_count = failed_count
        self.errors = errors or []
        self.message = message

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "errors": self.errors,
            "message": self.message,
        }


async def monthly_settlement_job(year_month: Optional[str] = None) -> BatchJobResult:
    """
    Monthly settlement calculation job.

    Runs on the 1st of each month to calculate settlements for the previous month.
    Delegates business logic to CalculateSettlementUseCase.

    Args:
        year_month: Year-month string in format "YYYY-MM" (defaults to previous month)

    Returns:
        BatchJobResult with processing statistics
    """
    if not settings.BATCH_JOBS_ENABLED:
        return BatchJobResult(success=True, message="Batch jobs disabled")

    # Determine target month
    if year_month is None:
        today = date.today()
        if today.month == 1:
            target_date = date(today.year - 1, 12, 1)
        else:
            target_date = date(today.year, today.month - 1, 1)
        year_month = target_date.strftime("%Y-%m")

    try:
        async for db in get_async_session():
            # Initialize use case with repository
            settlement_repo = SettlementRepository(db)
            use_case = CalculateSettlementUseCase(settlement_repo=settlement_repo)

            # Calculate settlements for all tutors
            result = await use_case.calculate_all_tutors_settlement(year_month, db)

            message = (
                f"Monthly settlement calculation completed for {year_month}. "
                f"Processed: {result['processed']}, Failed: {result['failed']}"
            )

            return BatchJobResult(
                success=True,
                processed_count=result["processed"],
                failed_count=result["failed"],
                message=message,
            )

    except Exception as e:
        return BatchJobResult(
            success=False,
            errors=[f"Job failed: {str(e)}"],
            message=f"Monthly settlement job failed: {str(e)}",
        )


async def payment_disbursement_job(year_month: Optional[str] = None) -> BatchJobResult:
    """
    Payment disbursement job for settled settlements.

    This job would handle the actual bank transfer to tutors.
    For MVP, this is a placeholder that marks settlements as "paid".

    Args:
        year_month: Year-month string in format "YYYY-MM"

    Returns:
        BatchJobResult with processing statistics
    """
    if not settings.BATCH_JOBS_ENABLED:
        return BatchJobResult(success=True, message="Batch jobs disabled")

    processed = 0
    failed = 0
    errors = []

    try:
        async for db in get_async_session():
            # Get pending settlements for the target month (or all pending)
            query = select(SettlementModel).where(SettlementModel.is_paid == False)

            if year_month:
                query = query.where(SettlementModel.year_month == year_month)

            result = await db.execute(query)
            settlements = result.scalars().all()

            for settlement in settlements:
                try:
                    # TODO: Integrate with actual bank transfer API
                    # For MVP, just mark as paid
                    settlement.is_paid = True
                    settlement.paid_at = datetime.utcnow()
                    processed += 1

                except Exception as e:
                    failed += 1
                    errors.append(f"Settlement {settlement.id}: {str(e)}")

            await db.commit()

            message = (
                f"Payment disbursement completed. "
                f"Processed: {processed}, Failed: {failed}"
            )

            return BatchJobResult(
                success=True,
                processed_count=processed,
                failed_count=failed,
                errors=errors,
                message=message,
            )

    except Exception as e:
        return BatchJobResult(
            success=False,
            errors=[f"Job failed: {str(e)}"],
            message=f"Payment disbursement job failed: {str(e)}",
        )


# Celery Beat integration example
try:
    from celery import Celery
    from celery.schedules import crontab

    celery_app = Celery(
        "tutorflow_settlement",
        broker=getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0"),
        backend=getattr(settings, "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    )

    @celery_app.task
    def celery_monthly_settlement_task(year_month: Optional[str] = None):
        """Celery task wrapper for monthly settlement job."""
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(monthly_settlement_job(year_month))
        return result.to_dict()

    @celery_app.task
    def celery_payment_disbursement_task(year_month: Optional[str] = None):
        """Celery task wrapper for payment disbursement job."""
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(payment_disbursement_job(year_month))
        return result.to_dict()

    # Celery Beat schedule configuration
    celery_app.conf.beat_schedule = {
        "monthly-settlement": {
            "task": "tasks.settlement_jobs.celery_monthly_settlement_task",
            "schedule": crontab(hour=2, minute=0, day_of_month=1),
        },
        "payment-disbursement": {
            "task": "tasks.settlement_jobs.celery_payment_disbursement_task",
            "schedule": crontab(hour=10, minute=0, day_of_month=5),
        },
    }

    CELERY_AVAILABLE = True

except ImportError:
    CELERY_AVAILABLE = False
    celery_app = None
