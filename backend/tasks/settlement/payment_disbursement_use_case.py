"""Payment disbursement use case."""
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.persistence.models import SettlementModel


class PaymentDisbursementUseCase:
    """Use case for processing payment disbursements."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def disburse_payments(self, year_month: Optional[str] = None) -> dict:
        """
        Disburse payments for pending settlements.

        Args:
            year_month: Year-month string in format "YYYY-MM"

        Returns:
            Dict with processed, failed, errors keys
        """
        processed = 0
        failed = 0
        errors = []

        # Get pending settlements for the target month (or all pending)
        query = select(SettlementModel).where(SettlementModel.is_paid == False)

        if year_month:
            query = query.where(SettlementModel.year_month == year_month)

        result = await self.db.execute(query)
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

        await self.db.commit()

        return {
            "processed": processed,
            "failed": failed,
            "errors": errors,
        }
