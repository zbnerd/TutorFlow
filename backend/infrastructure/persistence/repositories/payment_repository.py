"""Payment repository implementation."""
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Payment, PaymentStatus, Money
from domain.ports import PaymentRepositoryPort
from infrastructure.persistence.models import PaymentModel
from infrastructure.persistence.repositories.audit_log_repository import AuditLogRepository


class PaymentRepository(PaymentRepositoryPort):
    """SQLAlchemy implementation of PaymentRepositoryPort."""

    def __init__(self, session: AsyncSession, audit_repo: Optional[AuditLogRepository] = None):
        """Initialize repository with database session and optional audit repository."""
        self.session = session
        self.audit_repo = audit_repo

    async def save(
        self,
        payment: Payment,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Payment:
        """Save payment to database (create or update)."""
        if payment.id is None:
            # Create new payment
            new_values = {
                "booking_id": payment.booking_id,
                "amount": payment.amount.amount_krw if payment.amount else 0,
                "fee_rate": payment.fee_rate,
                "fee_amount": payment.fee_amount.amount_krw if payment.fee_amount else 0,
                "net_amount": payment.net_amount.amount_krw if payment.net_amount else 0,
                "pg_payment_key": payment.pg_payment_key,
                "pg_provider": payment.pg_provider,
                "status": payment.status.value if isinstance(payment.status, PaymentStatus) else payment.status,
            }
            db_payment = PaymentModel(
                booking_id=payment.booking_id,
                amount=payment.amount.amount_krw if payment.amount else 0,
                fee_rate=payment.fee_rate,
                fee_amount=payment.fee_amount.amount_krw if payment.fee_amount else 0,
                net_amount=payment.net_amount.amount_krw if payment.net_amount else 0,
                pg_payment_key=payment.pg_payment_key,
                pg_provider=payment.pg_provider,
                status=payment.status,
                paid_at=payment.paid_at,
                refunded_at=payment.refunded_at,
                refund_reason=payment.refund_reason,
            )
            self.session.add(db_payment)
            await self.session.flush()
            await self.session.refresh(db_payment)

            # Log creation
            if self.audit_repo:
                await self.audit_repo.log_change(
                    entity_type="payment",
                    entity_id=db_payment.id,
                    action="create",
                    old_value=None,
                    new_value=new_values,
                    actor_id=actor_id,
                    ip_address=ip_address,
                )

            return self._to_entity(db_payment)
        else:
            # Update existing payment
            result = await self.session.execute(
                select(PaymentModel).where(PaymentModel.id == payment.id)
            )
            db_payment = result.scalar_one_or_none()
            if db_payment:
                # Capture old values for audit
                old_values = {
                    "status": db_payment.status.value if isinstance(db_payment.status, PaymentStatus) else db_payment.status,
                    "paid_at": db_payment.paid_at.isoformat() if db_payment.paid_at else None,
                    "refunded_at": db_payment.refunded_at.isoformat() if db_payment.refunded_at else None,
                    "refund_reason": db_payment.refund_reason,
                }

                db_payment.status = payment.status
                db_payment.paid_at = payment.paid_at
                db_payment.refunded_at = payment.refunded_at
                db_payment.refund_reason = payment.refund_reason
                await self.session.flush()
                await self.session.refresh(db_payment)

                # Capture new values for audit
                new_values = {
                    "status": payment.status.value if isinstance(payment.status, PaymentStatus) else payment.status,
                    "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
                    "refunded_at": payment.refunded_at.isoformat() if payment.refunded_at else None,
                    "refund_reason": payment.refund_reason,
                }

                # Log update if something changed
                if self.audit_repo and old_values != new_values:
                    await self.audit_repo.log_change(
                        entity_type="payment",
                        entity_id=db_payment.id,
                        action="update",
                        old_value=old_values,
                        new_value=new_values,
                        actor_id=actor_id,
                        ip_address=ip_address,
                    )

                return self._to_entity(db_payment)
            return payment

    async def find_by_id(self, payment_id: int) -> Optional[Payment]:
        """Find payment by ID."""
        result = await self.session.execute(
            select(PaymentModel).where(PaymentModel.id == payment_id)
        )
        db_payment = result.scalar_one_or_none()
        return self._to_entity(db_payment) if db_payment else None

    async def find_by_booking_id(self, booking_id: int) -> Optional[Payment]:
        """Find payment by booking ID."""
        result = await self.session.execute(
            select(PaymentModel).where(PaymentModel.booking_id == booking_id)
        )
        db_payment = result.scalar_one_or_none()
        return self._to_entity(db_payment) if db_payment else None

    async def find_by_pg_key(self, pg_payment_key: str) -> Optional[Payment]:
        """Find payment by payment gateway key."""
        result = await self.session.execute(
            select(PaymentModel).where(PaymentModel.pg_payment_key == pg_payment_key)
        )
        db_payment = result.scalar_one_or_none()
        return self._to_entity(db_payment) if db_payment else None

    async def update_status(
        self,
        payment_id: int,
        new_status: PaymentStatus,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[Payment]:
        """Update payment status with audit logging."""
        result = await self.session.execute(
            select(PaymentModel).where(PaymentModel.id == payment_id)
        )
        db_payment = result.scalar_one_or_none()

        if not db_payment:
            return None

        old_status = db_payment.status
        db_payment.status = new_status
        await self.session.flush()
        await self.session.refresh(db_payment)

        # Log status change
        if self.audit_repo and old_status != new_status:
            await self.audit_repo.log_change(
                entity_type="payment",
                entity_id=payment_id,
                action="status_change",
                old_value={"status": old_status.value if isinstance(old_status, PaymentStatus) else old_status},
                new_value={"status": new_status.value if isinstance(new_status, PaymentStatus) else new_status},
                actor_id=actor_id,
                ip_address=ip_address,
            )

        return self._to_entity(db_payment)

    def _to_entity(self, db_payment: PaymentModel) -> Payment:
        """Convert ORM model to domain entity."""
        return Payment(
            id=db_payment.id,
            booking_id=db_payment.booking_id,
            amount=Money(db_payment.amount) if db_payment.amount else None,
            fee_rate=float(db_payment.fee_rate) if db_payment.fee_rate else 0.05,
            fee_amount=Money(db_payment.fee_amount) if db_payment.fee_amount else None,
            net_amount=Money(db_payment.net_amount) if db_payment.net_amount else None,
            pg_payment_key=db_payment.pg_payment_key,
            pg_provider=db_payment.pg_provider,
            status=db_payment.status,
            paid_at=db_payment.paid_at,
            refunded_at=db_payment.refunded_at,
            refund_reason=db_payment.refund_reason,
            created_at=db_payment.created_at,
            updated_at=db_payment.updated_at,
        )
