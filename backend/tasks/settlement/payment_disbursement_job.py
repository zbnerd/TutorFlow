"""Payment disbursement batch job.

Marks settled settlements as paid.
"""
from datetime import datetime
from typing import Optional

from config import settings
from infrastructure.database import get_async_session
from tasks.jobs.base import BatchJobResult
from tasks.settlement.payment_disbursement_use_case import PaymentDisbursementUseCase


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
            use_case = PaymentDisbursementUseCase(db)
            result = await use_case.disburse_payments(year_month)

            processed = result.get("processed", 0)
            failed = result.get("failed", 0)
            errors = result.get("errors", [])

            message = (
                f"Payment disbursement completed. "
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
            message=f"Payment disbursement job failed: {str(e)}",
        )
