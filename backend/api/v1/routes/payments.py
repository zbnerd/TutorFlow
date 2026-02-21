"""Payment API routes for Toss Payments integration."""
from typing import Annotated

from api.v1.routes.dependencies import get_current_user, get_repository_factory
from application.dto import ErrorResponse
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
from application.use_cases.payment import PaymentUseCases
from config import settings
from domain.entities import User
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import get_db
from infrastructure.external.payments import TossPaymentsAdapter
from infrastructure.persistence.repository_factory import RepositoryFactory

router = APIRouter()

# Get fee rate from config
FEE_RATE = getattr(settings, 'TOSS_PAYMENTS_FEE_RATE', 0.05)


@router.post("/prepare", response_model=PreparePaymentResponse)
async def prepare_payment(
    request: PreparePaymentRequest,
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PreparePaymentResponse:
    """Prepare payment for booking.

    This endpoint generates a payment key and order ID for the frontend
    to use when calling Toss Payments SDK.

    Args:
        request: Payment preparation request
        db: Database session
        current_user: Authenticated user

    Returns:
        Payment preparation details

    Raises:
        HTTPException 404: If booking not found
        HTTPException 400: If invalid amount
    """
    booking_repo = BookingRepository(db)
    payment_repo = PaymentRepository(db)
    payment_gateway = TossPaymentsAdapter()

    # Verify booking exists
    booking = await booking_repo.find_by_id(int(request.booking_id))
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="BOOKING_NOT_FOUND",
                message="Booking not found",
            ).model_dump(),
        )

    user_id = current_user.id

    payment_use_cases = PaymentUseCases(
        payment_gateway=payment_gateway,
        payment_repo=payment_repo,
        booking_repo=booking_repo,
        fee_rate=FEE_RATE,
    )

    try:
        return await payment_use_cases.prepare_payment(
            booking_id=int(request.booking_id),
            amount=request.amount,
            order_name=request.order_name,
            user_id=user_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_REQUEST",
                message=str(e),
            ).model_dump(),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                code="PAYMENT_PREPARATION_FAILED",
                message=f"Payment preparation failed: {str(e)}",
            ).model_dump(),
        ) from e


@router.post("/confirm", response_model=ConfirmPaymentResponse)
async def confirm_payment(
    request: ConfirmPaymentRequest,
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
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
        HTTPException 400: If payment verification fails
    """
    payment_gateway = TossPaymentsAdapter()

    payment_use_cases = PaymentUseCases(
        payment_gateway=payment_gateway,
        payment_repo=repos.payment(),
        booking_repo=repos.booking(),
        fee_rate=FEE_RATE,
    )

    try:
        return await payment_use_cases.confirm_payment(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_REQUEST",
                message=str(e),
            ).model_dump(),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                code="PAYMENT_CONFIRMATION_FAILED",
                message=f"Payment confirmation failed: {str(e)}",
            ).model_dump(),
        ) from e


@router.post("/{payment_key}/cancel", response_model=CancelPaymentResponse)
async def cancel_payment(
    payment_key: str,
    request: CancelPaymentRequest,
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
) -> CancelPaymentResponse:
    """Cancel a payment.

    Args:
        payment_key: Payment key to cancel
        request: Cancellation request
        db: Database session

    Returns:
        Cancellation details

    Raises:
        HTTPException 404: If payment not found
        HTTPException 400: If cancellation fails
    """
    payment_gateway = TossPaymentsAdapter()

    payment_use_cases = PaymentUseCases(
        payment_gateway=payment_gateway,
        payment_repo=repos.payment(),
        booking_repo=repos.booking(),
        fee_rate=FEE_RATE,
    )

    try:
        return await payment_use_cases.cancel_payment(payment_key, request)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                code="INVALID_REQUEST",
                message=str(e),
            ).model_dump(),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_REQUEST",
                message=str(e),
            ).model_dump(),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                code="PAYMENT_CANCELLATION_FAILED",
                message=f"Payment cancellation failed: {str(e)}",
            ).model_dump(),
        ) from e


@router.get("/{payment_key}", response_model=PaymentStatusResponse)
async def get_payment_status(
    payment_key: str,
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
) -> PaymentStatusResponse:
    """Get payment status.

    Args:
        payment_key: Payment key
        db: Database session

    Returns:
        Payment status details

    Raises:
        HTTPException 404: If payment not found
    """
    payment_gateway = TossPaymentsAdapter()

    payment_use_cases = PaymentUseCases(
        payment_gateway=payment_gateway,
        payment_repo=repos.payment(),
        booking_repo=repos.booking(),
        fee_rate=FEE_RATE,
    )

    try:
        return await payment_use_cases.get_payment_status(payment_key)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                code="INVALID_REQUEST",
                message=str(e),
            ).model_dump(),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_REQUEST",
                message=str(e),
            ).model_dump(),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                code="PAYMENT_STATUS_FAILED",
                message=f"Failed to get payment status: {str(e)}",
            ).model_dump(),
        ) from e


@router.get("/booking/{booking_id}/refund-estimate", response_model=RefundEstimateResponse)
async def get_refund_estimate(
    booking_id: int,
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
) -> RefundEstimateResponse:
    """Calculate refund estimate for a booking.

    Args:
        booking_id: Booking ID
        db: Database session

    Returns:
        Refund estimate breakdown

    Raises:
        HTTPException 404: If booking or payment not found
        HTTPException 400: If no payment found
    """
    payment_gateway = TossPaymentsAdapter()

    payment_use_cases = PaymentUseCases(
        payment_gateway=payment_gateway,
        payment_repo=repos.payment(),
        booking_repo=repos.booking(),
        fee_rate=FEE_RATE,
    )

    try:
        return await payment_use_cases.calculate_refund_estimate(booking_id)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                code="INVALID_REQUEST",
                message=str(e),
            ).model_dump(),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_REQUEST",
                message=str(e),
            ).model_dump(),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                code="REFUND_ESTIMATE_FAILED",
                message=f"Failed to calculate refund estimate: {str(e)}",
            ).model_dump(),
        ) from e


@router.post("/webhooks/toss")
async def toss_webhook(
    request: Request,
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
) -> dict:
    """Handle Toss Payments webhook.

    Verifies signature and updates payment status.

    Args:
        request: FastAPI Request object
        db: Database session

    Returns:
        Webhook processing result

    Raises:
        HTTPException 401: If signature verification fails
        HTTPException 400: If invalid payload
    """
    booking_repo = BookingRepository(db)
    payment_repo = PaymentRepository(db)
    payment_gateway = TossPaymentsAdapter()

    # Get raw body for signature verification
    raw_body = await request.body()

    # Verify signature
    signature = request.headers.get("Toss-Signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                code="MISSING_SIGNATURE",
                message="Missing Toss-Signature header",
            ).model_dump(),
        )

    if not payment_gateway.verify_webhook_signature(
        payload=raw_body.decode(),
        signature=signature,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                code="INVALID_SIGNATURE",
                message="Invalid signature",
            ).model_dump(),
        )

    # Parse webhook data
    try:
        webhook_data = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_JSON",
                message="Invalid JSON payload",
            ).model_dump(),
        ) from e

    payment_use_cases = PaymentUseCases(
        payment_gateway=payment_gateway,
        payment_repo=payment_repo,
        booking_repo=booking_repo,
        fee_rate=FEE_RATE,
    )

    try:
        result = await payment_use_cases.handle_webhook(webhook_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                code="WEBHOOK_FAILED",
                message=f"Webhook processing failed: {str(e)}",
            ).model_dump(),
        ) from e
