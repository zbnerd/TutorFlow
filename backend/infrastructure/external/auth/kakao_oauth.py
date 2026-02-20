"""Kakao OAuth 2.0 adapter implementation."""
import httpx
from config import settings


class KakaoOAuthAdapter:
    """Kakao OAuth 2.0 implementation of OAuthPort."""

    KAKAO_AUTH_URL = "https://kauth.kakao.com"
    KAKAO_API_URL = "https://kapi.kakao.com"

    def __init__(self):
        """Initialize Kakao OAuth adapter."""
        self.client_id = settings.KAKAO_CLIENT_ID
        self.client_secret = settings.KAKAO_CLIENT_SECRET
        self.redirect_uri = settings.KAKAO_REDIRECT_URI

    async def exchange_code_for_token(self, code: str) -> dict:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from Kakao OAuth callback

        Returns:
            Dict containing access_token, refresh_token, expires_in, etc.

        Raises:
            httpx.HTTPError: If token exchange fails
        """
        url = f"{self.KAKAO_AUTH_URL}/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }

        # Add client_secret if provided (for confidential clients)
        if self.client_secret:
            data["client_secret"] = self.client_secret

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> dict:
        """
        Get user information from Kakao using access token.

        Args:
            access_token: Kakao access token

        Returns:
            Dict containing user information (id, properties, etc.)

        Raises:
            httpx.HTTPError: If user info request fails
        """
        url = f"{self.KAKAO_API_URL}/v2/user/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers)
            response.raise_for_status()
            return response.json()

    def get_authorization_url(self, state: str | None = None) -> str:
        """
        Generate Kakao OAuth authorization URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL to redirect user to Kakao login
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
        }

        if state:
            params["state"] = state

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.KAKAO_AUTH_URL}/oauth/authorize?{query_string}"
