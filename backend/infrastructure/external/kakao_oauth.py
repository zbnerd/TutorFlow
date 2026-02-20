"""Kakao OAuth adapter implementation."""
import httpx

from config import settings
from domain.ports import OAuthPort


class KakaoOAuthAdapter(OAuthPort):
    """Kakao OAuth 2.0 adapter."""

    def __init__(self):
        self.client_id = settings.KAKAO_CLIENT_ID
        self.client_secret = settings.KAKAO_CLIENT_SECRET
        self.redirect_uri = settings.KAKAO_REDIRECT_URI

    async def get_user_info(self, access_token: str) -> dict:
        """Get user information from Kakao."""
        async with httpx.AsyncClient() as client:
            # Get user profile
            response = await client.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

            return {
                "oauth_id": str(data.get("id")),
                "email": data.get("kakao_account", {}).get("email"),
                "name": None,  # Kakao doesn't provide name by default
                "phone": data.get("kakao_account", {}).get("phone_number"),
                "profile_image_url": data.get("kakao_account", {}).get("profile", {}).get("profile_image_url"),
            }

    async def get_access_token(self, code: str) -> dict:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://kauth.kakao.com/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "code": code,
                },
            )
            response.raise_for_status()
            return response.json()
