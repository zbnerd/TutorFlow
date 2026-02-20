"""Toss Payments adapter implementation."""
import httpx

from config import settings
from domain.ports import PaymentPort


class TossPaymentsAdapter(PaymentPort):
    """Toss Payments API adapter."""

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
        """Create a payment request."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/payments",
                headers={
                    "Authorization": f"Basic {self._encode_auth()}",
                },
                json={
                    "amount": amount,
                    "orderId": f"booking-{booking_id}",
                    "orderName": order_name,
                },
            )
            response.raise_for_status()
            return response.json()

    async def verify_payment(self, payment_key: str, amount: int) -> dict:
        """Verify payment status."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/payments/{payment_key}",
                headers={
                    "Authorization": f"Basic {self._encode_auth()}",
                },
            )
            response.raise_for_status()
            data = response.json()

            # Verify amount matches
            if data.get("amount") != amount:
                raise ValueError(f"Amount mismatch: expected {amount}, got {data.get('amount')}")

            return data

    async def cancel_payment(self, payment_key: str, cancel_reason: str) -> dict:
        """Cancel a payment."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/payments/{payment_key}/cancel",
                headers={
                    "Authorization": f"Basic {self._encode_auth()}",
                },
                json={"cancelReason": cancel_reason},
            )
            response.raise_for_status()
            return response.json()

    def _encode_auth(self) -> str:
        """Encode API key for Basic Auth."""
        import base64

        credentials = f"{self.api_key}:{self.secret_key}"
        return base64.b64encode(credentials.encode()).decode()
