"""Payment use cases with complete Toss Payments integration."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from application.dto.payment import (
    CancelPaymentRequest,
    CancelPaymentResponse,
    ConfirmPaymentRequest,
    ConfirmPaymentResponse,
    PreparePaymentRequest,
    PreparePaymentResponse,
    RefundEstimateResponse,
    PaymentStatusResponse,
)
from domain.entities import Booking, Payment, PaymentStatus, BookingStatus, Money
from domain.ports import PaymentPort, PaymentRepositoryPort, BookingRepositoryPort


@dataclass
class PaymentUseCases:
    """Payment-related business logic."""

    payment_gateway: PaymentPort
    payment_repo: PaymentRepositoryPort
    booking_repo: BookingRepositoryPort
    fee_rate: float = 0.05  # Default 5% platform fee

    async def prepare_payment(
        self,
        booking_id: int,
        amount: int,
        order_name: str,
        user_id: int,
    ) -> PreparePaymentResponse:
        """
        Prepare payment with Toss Payments.

        Creates order_id and payment_key for frontend Toss SDK.

        Args:
            booking_id: Booking ID
            amount: Payment amount in KRW
            order_name: Order name
            user_id: User ID preparing payment

        Returns:
            PreparePaymentResponse with payment details
        """
        payment_data = await self.payment_gateway.create_payment(
            amount=amount,
            booking_id=booking_id,
            user_id=user_id,
            order_name=order_name,
        )

        return PreparePaymentResponse(
            payment_key=payment_data["payment_key"],
            order_id=payment_data["order_id"],
            amount=payment_data["amount"],
            customer_key=f"customer-{user_id}",
        )

    async def confirm_payment(
        self,
        request: ConfirmPaymentRequest,
    ) -> ConfirmPaymentResponse:
        """
        Confirm payment after user approval in Toss UI.

        Verifies payment with Toss, creates Payment record, updates booking status.

        Args:
            request: Confirm payment request with payment_key, order_id, amount

        Returns:
            ConfirmPaymentResponse with payment details

        Raises:
            ValueError: If payment verification fails, amount mismatch, or booking not found
        """
        # Extract booking_id from order_id
        # order_id format: "booking-{booking_id}-{timestamp}"
        order_id_parts = request.order_id.split("-")
        if len(order_id_parts) < 2 or order_id_parts[0] != "booking":
            raise ValueError(f"Invalid order_id format: {request.order_id}")

        booking_id = int(order_id_parts[1])

        # Get booking
        booking = await self.booking_repo.find_by_id(booking_id)
        if not booking:
            raise ValueError(f"Booking not found: {booking_id}")

        # Verify payment with Toss Payments
        payment_data = await self.payment_gateway.confirm_payment(
            payment_key=request.payment_key,
            order_id=request.order_id,
            amount=request.amount,
        )

        # Check payment status
        if payment_data["status"] != PaymentStatus.PAID:
            raise ValueError(f"Payment not successful: {payment_data['toss_status']}")

        # Calculate fees
        fee_rate = self.fee_rate
        fee_amount = int(request.amount * fee_rate)
        net_amount = request.amount - fee_amount

        # Create payment entity
        payment = Payment(
            booking_id=booking.id,
            amount=Money(request.amount),
            fee_rate=fee_rate,
            pg_payment_key=request.payment_key,
            pg_provider="toss",
            status=PaymentStatus.PAID,
            paid_at=datetime.utcnow(),
        )

        # Save payment
        payment = await self.payment_repo.save(payment)

        # Update booking status to APPROVED
        booking.status = BookingStatus.APPROVED
        await self.booking_repo.save(booking)

        return ConfirmPaymentResponse(
            payment_id=str(payment.id),
            booking_id=str(booking.id),
            payment_key=request.payment_key,
            order_id=request.order_id,
            amount=request.amount,
            fee_rate=fee_rate,
            fee_amount=fee_amount,
            net_amount=net_amount,
            status=PaymentStatus.PAID,
            payment_method=payment_data.get("method"),
            paid_at=datetime.utcnow(),
        )

    async def cancel_payment(
        self,
        payment_key: str,
        request: CancelPaymentRequest,
    ) -> CancelPaymentResponse:
        """
        Cancel a payment.

        Calls Toss API to cancel and updates payment record.

        Args:
            payment_key: Payment key to cancel
            request: Cancellation request with reason

        Returns:
            CancelPaymentResponse

        Raises:
            ValueError: If payment not found or cancellation fails
        """
        # Find payment
        payment = await self.payment_repo.find_by_pg_key(payment_key)
        if not payment:
            raise ValueError(f"Payment not found: {payment_key}")

        # Call Toss Payments API to cancel
        cancel_data = await self.payment_gateway.cancel_payment(
            payment_key=payment_key,
            cancel_reason=request.cancel_reason,
        )

        # Update payment status
        payment.status = cancel_data["status"]
        payment.refunded_at = datetime.utcnow()
        payment.refund_reason = request.cancel_reason
        await self.payment_repo.save(payment)

        # If full refund, update booking status to CANCELLED
        if payment.status == PaymentStatus.REFUNDED:
            booking = await self.booking_repo.find_by_id(payment.booking_id)
            if booking:
                booking.status = BookingStatus.CANCELLED
                await self.booking_repo.save(booking)

        return CancelPaymentResponse(
            payment_id=str(payment.id),
            payment_key=payment_key,
            cancel_reason=request.cancel_reason,
            refund_amount=cancel_data.get(
                "amount", payment.amount.amount_krw if payment.amount else 0
            ),
            cancelled_at=datetime.utcnow(),
            status=payment.status,
        )

    async def get_payment_status(self, payment_key: str) -> PaymentStatusResponse:
        """
        Get payment status.

        Returns current payment status from database and Toss API.

        Args:
            payment_key: Payment key

        Returns:
            PaymentStatusResponse with full payment details

        Raises:
            ValueError: If payment not found
        """
        # Find payment in database
        payment = await self.payment_repo.find_by_pg_key(payment_key)
        if not payment:
            raise ValueError(f"Payment not found: {payment_key}")

        # Get latest status from Toss
        toss_data = await self.payment_gateway.get_payment_status(payment_key)

        return PaymentStatusResponse(
            id=payment.id,
            booking_id=payment.booking_id,
            amount=payment.amount.amount_krw if payment.amount else 0,
            fee_rate=payment.fee_rate,
            fee_amount=payment.fee_amount.amount_krw if payment.fee_amount else 0,
            net_amount=payment.net_amount.amount_krw if payment.net_amount else 0,
            pg_payment_key=payment.pg_payment_key,
            pg_provider=payment.pg_provider,
            status=payment.status.value,
            paid_at=payment.paid_at,
            refunded_at=payment.refunded_at,
            refund_reason=payment.refund_reason,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            method=toss_data.get("method"),
            receipt_url=toss_data.get("receipt_url"),
        )

    async def calculate_refund_estimate(
        self,
        booking_id: int,
    ) -> RefundEstimateResponse:
        """
        Calculate refund estimate for a booking.

        Args:
            booking_id: Booking ID

        Returns:
            RefundEstimateResponse with breakdown

        Raises:
            ValueError: If booking or payment not found
        """
        # Get booking
        booking = await self.booking_repo.find_by_id(booking_id)
        if not booking:
            raise ValueError(f"Booking not found: {booking_id}")

        # Get payment
        payment = await self.payment_repo.find_by_booking_id(booking_id)
        if not payment or payment.status != PaymentStatus.PAID:
            raise ValueError(f"No paid payment found for booking: {booking_id}")

        total_paid = payment.amount.amount_krw if payment.amount else 0
        total_sessions = booking.total_sessions or 0
        completed_sessions = booking.completed_sessions or 0
        remaining_sessions = total_sessions - completed_sessions

        # Calculate session rate
        session_rate = total_paid // total_sessions if total_sessions > 0 else 0

        # Calculate refund amount (based on remaining sessions)
        refund_amount = session_rate * remaining_sessions

        # Platform fee is proportional to refund
        platform_fee = int(refund_amount * payment.fee_rate)

        # PG fee is typically not refundable
        pg_fee = 0

        return RefundEstimateResponse(
            booking_id=str(booking.id),
            total_paid=total_paid,
            total_sessions=total_sessions,
            completed_sessions=completed_sessions,
            remaining_sessions=remaining_sessions,
            session_rate=session_rate,
            refund_amount=refund_amount,
            platform_fee=platform_fee,
            pg_fee=pg_fee,
        )

    async def handle_webhook(self, webhook_data: dict) -> dict:
        """
        Handle Toss Payments webhook.

        Updates payment status based on webhook notification.

        Args:
            webhook_data: Webhook payload from Toss

        Returns:
            Webhook processing result
        """
        payment_key = webhook_data.get("payment_key")
        toss_status = webhook_data.get("status")

        if not payment_key or not toss_status:
            return {"status": "error", "message": "Invalid webhook data"}

        # Find payment
        payment = await self.payment_repo.find_by_pg_key(payment_key)
        if not payment:
            return {"status": "error", "message": "Payment not found"}

        # Map Toss status to our status
        status_map = {
            "DONE": PaymentStatus.PAID,
            "CANCELED": PaymentStatus.REFUNDED,
            "PARTIAL_CANCELED": PaymentStatus.PARTIALLY_REFUNDED,
            "FAILED": PaymentStatus.FAILED,
            "EXPIRED": PaymentStatus.FAILED,
        }

        new_status = status_map.get(toss_status)
        if new_status:
            payment.status = new_status

            if new_status == PaymentStatus.PAID:
                payment.paid_at = datetime.utcnow()
                # Update booking to APPROVED
                booking = await self.booking_repo.find_by_id(payment.booking_id)
                if booking and booking.status == BookingStatus.PENDING:
                    booking.status = BookingStatus.APPROVED
                    await self.booking_repo.save(booking)

            elif new_status in (PaymentStatus.REFUNDED, PaymentStatus.PARTIALLY_REFUNDED):
                payment.refunded_at = datetime.utcnow()
                # Update booking to CANCELLED if full refund
                if new_status == PaymentStatus.REFUNDED:
                    booking = await self.booking_repo.find_by_id(payment.booking_id)
                    if booking:
                        booking.status = BookingStatus.CANCELLED
                        await self.booking_repo.save(booking)

            await self.payment_repo.save(payment)

        return {
            "status": "processed",
            "payment_key": payment_key,
            "webhook_status": toss_status,
            "updated_status": new_status.value if new_status else None,
        }
