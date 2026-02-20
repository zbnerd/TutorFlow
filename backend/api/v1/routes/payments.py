"""Payment API routes."""
import hmac
import hashlib
import base64
from typing import Annotated

from application.dto.payment import (
    CancelPaymentRequest,
    CancelPaymentResponse,
    ConfirmPaymentRequest,
    ConfirmPaymentResponse,
    PreparePaymentRequest,
    PreparePaymentResponse,
    RefundEstimateResponse,
    TossWebhookRequest,
)
from application.use_cases.payment import PaymentUseCases
from config import settings
from fastapi import APIRouter, Depends, Header, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import get_db

router = APIRouter()
payment_use_cases = PaymentUseCases()


def verify_webhook_signature(
    body: bytes,
    signature: str,
    secret: str = settings.TOSS_PAYMENTS_SECRET_KEY,
) -> bool:
    """Verify Toss webhook signature.

    Args:
        body: Raw request body
        signature: Toss-Signature header value
        secret: Toss Payments secret key

    Returns:
        True if signature is valid
    """
    if not signature:
        return False

    # Toss uses HMAC-SHA256
    # Format: "BASE64(HMAC-SHA256(secret, body))"
    expected_hmac = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256,
    ).digest()
    expected_signature = base64.b64encode(expected_hmac).decode()

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_signature, signature)


@router.post("/prepare", response_model=PreparePaymentResponse)
async def prepare_payment(
    request: PreparePaymentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PreparePaymentResponse:
    """Prepare payment for booking.

    This endpoint generates a payment key and order ID for the frontend
    to use when calling Toss Payments SDK.

    Args:
        request: Payment preparation request
        db: Database session

    Returns:
        Payment preparation details
    """
    # In production, verify booking exists and calculate amount
    # booking = await booking_repository.find_by_id(request.booking_id)
    # if not booking:
    #     raise HTTPException(status_code=404, detail="Booking not found")

    return await payment_use_cases.prepare_payment(
        booking_id=request.booking_id,
        amount=request.amount,
        order_name=request.order_name,
    )


@router.post("/confirm", response_model=ConfirmPaymentResponse)
async def confirm_payment(
    request: ConfirmPaymentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConfirmPaymentResponse:
    """Confirm payment after user approval.

    This endpoint verifies the payment with Toss Payments
    and updates the booking status.

    Args:
        request: Payment confirmation request
        db: Database session

    Returns:
        Payment confirmation details

    Raises:
        HTTPException: If payment verification fails
    """
    try:
        # In production, fetch booking from database
        # booking = await booking_repository.find_by_id(request.order_id)
        # if not booking:
        #     raise HTTPException(status_code=404, detail="Booking not found")

        # Mock booking for now
        from domain.entities import Booking

        mock_booking = Booking(id=request.order_id, total_sessions=10)

        return await payment_use_cases.confirm_payment(request, mock_booking)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/{payment_key}/cancel", response_model=CancelPaymentResponse)
async def cancel_payment(
    payment_key: str,
    request: CancelPaymentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CancelPaymentResponse:
    """Cancel a payment.

    Args:
        payment_key: Payment key to cancel
        request: Cancellation request
        db: Database session

    Returns:
        Cancellation details

    Raises:
        HTTPException: If cancellation fails
    """
    try:
        return await payment_use_cases.cancel_payment(payment_key, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{payment_key}")
async def get_payment_status(
    payment_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get payment status.

    Args:
        payment_key: Payment key
        db: Database session

    Returns:
        Payment status details
    """
    return await payment_use_cases.get_payment_status(payment_key)


@router.get("/bookings/{booking_id}/refund-estimate", response_model=RefundEstimateResponse)
async def get_refund_estimate(
    booking_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RefundEstimateResponse:
    """Calculate refund estimate for a booking.

    Args:
        booking_id: Booking ID
        db: Database session

    Returns:
        Refund estimate breakdown
    """
    # In production, fetch booking and payment from database
    # booking = await booking_repository.find_by_id(booking_id)
    # payment = await payment_repository.find_by_booking_id(booking_id)

    # Mock data for now
    from domain.entities import Booking

    mock_booking = Booking(id=booking_id, total_sessions=10, completed_sessions=3)

    return await payment_use_cases.calculate_refund_estimate(
        booking=mock_booking,
        total_paid=500000,  # Mock amount
    )
