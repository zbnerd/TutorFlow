"""Monthly settlement batch jobs for TutorFlow.

This module provides scheduled jobs for calculating and processing
monthly tutor settlements.

Jobs can be scheduled using Celery Beat, APScheduler, or any cron-compatible scheduler.
Runs on the 1st of each month to calculate settlements for the previous month.
"""
import asyncio
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func as sql_func

from config import settings
from domain.entities import Settlement, SettlementStatus, Money, SessionStatus, BookingStatus
from infrastructure.database import get_async_session
from infrastructure.persistence.models import (
    SettlementModel,
    BookingSessionModel,
    BookingModel,
    TutorModel,
    PaymentModel,
)


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
    created_settlements = []

    try:
        async for db in get_async_session():
            # Get all tutors who have completed sessions in the target month
            tutor_revenue = await _calculate_tutor_revenue(db, month_start, month_end)

            for tutor_id, revenue_data in tutor_revenue.items():
                try:
                    # Check if settlement already exists
                    existing = await _get_existing_settlement(db, tutor_id, year_month)
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
                    platform_fee_amount = int(total_amount * 0.05)  # 5%
                    pg_fee_amount = int(total_amount * 0.03)  # 3%
                    net_amount = total_amount - platform_fee_amount - pg_fee_amount

                    # Create settlement record
                    settlement = SettlementModel(
                        tutor_id=tutor_id,
                        year_month=year_month,
                        total_sessions=total_sessions,
                        total_amount=total_amount,
                        total_fee=platform_fee_amount + pg_fee_amount,  # For backward compatibility
                        net_amount=net_amount,
                        is_paid=False,
                        paid_at=None,
                        created_at=datetime.utcnow(),
                    )

                    db.add(settlement)
                    await db.flush()

                    created_settlements.append({
                        "tutor_id": tutor_id,
                        "year_month": year_month,
                        "total_sessions": total_sessions,
                        "total_amount": total_amount,
                        "platform_fee": platform_fee_amount,
                        "pg_fee": pg_fee_amount,
                        "net_amount": net_amount,
                    })

                    processed += 1

                except Exception as e:
                    failed += 1
                    errors.append(f"Tutor {tutor_id}: {str(e)}")

            # Commit all settlements
            await db.commit()

            message = (
                f"Monthly settlement calculation completed for {year_month}. "
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
            message=f"Monthly settlement job failed: {str(e)}",
        )


async def _calculate_tutor_revenue(
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
        # Note: This assumes 1-hour sessions. For variable-length sessions,
        # you'd need to store session_duration in BookingSessionModel
        total_amount = (hourly_rate or 0) * session_count

        tutor_revenue[tutor_id] = {
            "total_amount": total_amount,
            "total_sessions": session_count,
        }

    return tutor_revenue


async def _get_existing_settlement(
    db: AsyncSession,
    tutor_id: int,
    year_month: str,
) -> Optional[SettlementModel]:
    """Check if a settlement already exists for the tutor and month."""
    result = await db.execute(
        select(SettlementModel).where(
            and_(
                SettlementModel.tutor_id == tutor_id,
                SettlementModel.year_month == year_month,
            )
        )
    )
    return result.scalar_one_or_none()


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
        broker=settings.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        backend=settings.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
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
            "schedule": crontab(hour=2, minute=0, day_of_month=1),  # 02:00 on 1st of each month
        },
        # Payment disbursement would typically run a few days after settlement
        "payment-disbursement": {
            "task": "tasks.settlement_jobs.celery_payment_disbursement_task",
            "schedule": crontab(hour=10, minute=0, day_of_month=5),  # 10:00 on 5th of each month
        },
    }

    CELERY_AVAILABLE = True

except ImportError:
    CELERY_AVAILABLE = False
    celery_app = None
