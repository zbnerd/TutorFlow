"""Toss Payments adapter implementation with complete payment flow support."""
import base64
import hashlib
import hmac
from datetime import datetime
from typing import Optional

import httpx

from config import settings
from domain.entities import Payment, PaymentStatus
from domain.ports import PaymentPort


class TossPaymentsAdapter(PaymentPort):
    """Toss Payments API adapter with enhanced payment support."""

    def __init__(self):
        self.api_key = settings.TOSS_PAYMENTS_API_KEY
        self.secret_key = settings.TOSS_PAYMENTS_SECRET_KEY
        self.api_url = settings.TOSS_PAYMENTS_API_URL

    async def create_payment(
        self,
        amount: int,
        booking_id: int,
        user_id: int,
        order_name: str,
    ) -> dict:
        """
        Prepare payment by creating payment key/orderId.

        Returns payment details including payment_key for frontend.
        """
        order_id = f"booking-{booking_id}-{int(datetime.utcnow().timestamp())}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_url}/payments/prepare",
                headers={
                    "Authorization": f"Basic {self._encode_auth()}",
                    "Content-Type": "application/json",
                },
                json={
                    "amount": amount,
                    "orderId": order_id,
                    "orderName": order_name,
                    "customerEmail": "",  # Will be filled by frontend
                },
            )
            response.raise_for_status()
            data = response.json()
            return {
                "payment_key": data.get("paymentKey", order_id),
                "order_id": order_id,
                "amount": amount,
                "order_name": order_name,
            }

    async def confirm_payment(
        self,
        payment_key: str,
        order_id: str,
        amount: int,
    ) -> dict:
        """
        Confirm payment after user approval in Toss UI.

        Verifies payment with Toss API and returns payment details.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_url}/payments/confirm",
                headers={
                    "Authorization": f"Basic {self._encode_auth()}",
                    "Content-Type": "application/json",
                },
                json={
                    "paymentKey": payment_key,
                    "orderId": order_id,
                    "amount": amount,
                },
            )
            response.raise_for_status()
            return self._parse_payment_response(response.json())

    async def verify_payment(self, payment_key: str, amount: int) -> dict:
        """
        Verify payment status from Toss API.

        Raises ValueError if amount mismatch.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.api_url}/payments/{payment_key}",
                headers={
                    "Authorization": f"Basic {self._encode_auth()}",
                },
            )
            response.raise_for_status()
            data = response.json()

            # Verify amount matches
            total_amount = data.get("totalAmount", 0)
            if total_amount != amount:
                raise ValueError(f"Amount mismatch: expected {amount}, got {total_amount}")

            return self._parse_payment_response(data)

    async def cancel_payment(
        self,
        payment_key: str,
        cancel_reason: str,
        cancel_amount: Optional[int] = None,
    ) -> dict:
        """
        Cancel payment (full or partial).

        If cancel_amount is None, cancels full amount.
        """
        payload = {"cancelReason": cancel_reason}
        if cancel_amount is not None:
            payload["cancelAmount"] = cancel_amount

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_url}/payments/{payment_key}/cancel",
                headers={
                    "Authorization": f"Basic {self._encode_auth()}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            return self._parse_payment_response(response.json())

    async def get_payment_status(self, payment_key: str) -> dict:
        """Get current payment status."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.api_url}/payments/{payment_key}",
                headers={
                    "Authorization": f"Basic {self._encode_auth()}",
                },
            )
            response.raise_for_status()
            return self._parse_payment_response(response.json())

    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
    ) -> bool:
        """
        Verify webhook signature for security.

        Toss-Signature header format: base64(hmac_sha256(secret_key, payload))
        """
        if not signature:
            return False

        expected_signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode(),
                payload.encode(),
                hashlib.sha256,
            ).digest()
        ).decode()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature)

    def _parse_payment_response(self, data: dict) -> dict:
        """Parse Toss API response to standardized format."""
        status_map = {
            "READY": PaymentStatus.PENDING,
            "IN_PROGRESS": PaymentStatus.PENDING,
            "WAITING_FOR_DEPOSIT": PaymentStatus.PENDING,
            "DONE": PaymentStatus.PAID,
            "CANCELED": PaymentStatus.REFUNDED,
            "PARTIAL_CANCELED": PaymentStatus.PARTIALLY_REFUNDED,
            "ABORTED": PaymentStatus.FAILED,
            "EXPIRED": PaymentStatus.FAILED,
        }

        toss_status = data.get("status", "READY")
        payment_status = status_map.get(toss_status, PaymentStatus.PENDING)

        return {
            "payment_key": data.get("paymentKey"),
            "order_id": data.get("orderId"),
            "status": payment_status,
            "toss_status": toss_status,
            "amount": data.get("totalAmount", 0),
            "method": data.get("method", ""),  # 카드, 간편결제, 가상계좌 등
            "approved_at": data.get("approvedAt"),
            "canceled_at": (
                data.get("canceledAt", {}).get("canceledAt")
                if data.get("canceledAt")
                else None
            ),
            "card_info": data.get("card", {}),
            "virtual_account": data.get("virtualAccount", {}),
            "receipt_url": data.get("receipt", {}).get("url"),
        }

    def _encode_auth(self) -> str:
        """Encode API key for Basic Auth."""
        credentials = f"{self.api_key}:{self.secret_key}"
        return base64.b64encode(credentials.encode()).decode()
