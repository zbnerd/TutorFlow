"""Webhook handlers for external services."""
import hmac
import hashlib
import base64
import json
from typing import Annotated

from api.v1.routes.dependencies import get_payment_use_cases
from application.dto.payment import TossWebhookRequest
from application.use_cases.payment import PaymentUseCases
from config import settings
from fastapi import APIRouter, Depends, Header, Request, HTTPException, status
from pydantic import ValidationError

router = APIRouter()


def verify_toss_signature(body: bytes, signature: str) -> bool:
    """Verify Toss Payments webhook signature.

    Args:
        body: Raw request body
        signature: Toss-Signature header value

    Returns:
        True if signature is valid
    """
    if not signature:
        return False

    secret = settings.TOSS_PAYMENTS_SECRET_KEY

    # Toss uses HMAC-SHA256
    expected_hmac = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256,
    ).digest()
    expected_signature = base64.b64encode(expected_hmac).decode()

    # Use constant-time comparison
    return hmac.compare_digest(expected_signature, signature)


@router.post("/toss", status_code=status.HTTP_200_OK)
async def toss_webhook(
    request: Request,
    payment_use_cases: Annotated[PaymentUseCases, Depends(get_payment_use_cases)],
    toss_signature: Annotated[str | None, Header(alias="Toss-Signature")] = None,
) -> dict:
    """Handle Toss Payments webhooks.

    This endpoint receives payment status updates from Toss Payments.
    The signature is verified to ensure the request is from Toss.

    Webhook events:
    - DONE: Payment successful
    - CANCELED: Payment cancelled
    - FAILED: Payment failed
    - EXPIRED: Payment expired

    Args:
        request: FastAPI request object
        toss_signature: Toss-Signature header for verification
        payment_use_cases: Payment use cases dependency

    Returns:
        Confirmation response

    Raises:
        HTTPException: If signature verification fails or processing error
    """
    # Get raw body
    body = await request.body()

    # Verify signature
    if not verify_toss_signature(body, toss_signature or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    # Parse webhook data
    try:
        webhook_data = TossWebhookRequest(**json.loads(body.decode()))
    except (json.JSONDecodeError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook data: {e}",
        ) from e

    # Process webhook
    try:
        result = await payment_use_cases.handle_webhook(webhook_data.model_dump())
        return result
    except Exception as e:
        # Log error but return 200 to prevent Toss from retrying
        # In production, you should log this properly
        return {
            "status": "error",
            "message": str(e),
        }
