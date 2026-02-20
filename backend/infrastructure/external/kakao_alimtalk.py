"""Kakao Alimtalk adapter implementation."""
import httpx

from config import settings
from domain.ports import NotificationPort


class KakaoAlimtalkAdapter(NotificationPort):
    """Kakao Alimtalk notification adapter."""

    def __init__(self):
        self.api_key = settings.KAKAO_ALIMTalk_API_KEY
        self.sender = settings.KAKAO_ALIMTalk_SENDER

    async def send_sms(self, phone: str, message: str) -> bool:
        """Send SMS notification (fallback)."""
        # In production, integrate with SMS provider like CoolSMS
        print(f"SMS to {phone}: {message}")
        return True

    async def send_alimtalk(
        self,
        phone: str,
        template_code: str,
        variables: dict,
    ) -> bool:
        """Send Kakao Alimtalk notification."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api-alimtalk.cloud.toast.com/alimtalk/v2.5/applications",
                    headers={
                        "X-Secret-Key": self.api_key,
                        "Content-Type": "application/json;charset=UTF-8",
                    },
                    json={
                        "senderKey": self.sender,
                        "recipientNo": phone,
                        "templateCode": template_code,
                        "content": variables.get("content", ""),
                    },
                )
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Alimtalk failed, falling back to SMS: {e}")
            return await self.send_sms(phone, variables.get("content", ""))
