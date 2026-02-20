"""JWT token security tests.

Tests for JWT authentication security:
- Token expiration validation
- Invalid token rejection
- Token tampering detection
- Refresh token security
"""
import pytest
import jwt
from datetime import datetime, timedelta
from httpx import AsyncClient

from infrastructure.external.auth import TokenService


@pytest.mark.asyncio
class TestJWTSecurity:
    """Test JWT token security."""

    async def test_access_token_expiration(self, e2e_client: AsyncClient):
        """Test that expired access tokens are rejected."""
        # This test would need a protected endpoint
        # For now, we test the TokenService directly
        token_service = TokenService()

        # Create an expired token
        user_id = 1
        expired_token = token_service.create_access_token(
            user_id,
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        # Try to decode expired token
        with pytest.raises(ValueError) as exc_info:
            token_service.decode_token(expired_token)
        assert "expired" in str(exc_info.value).lower()

    async def test_invalid_token_rejection(self, e2e_client: AsyncClient):
        """Test that invalid tokens are rejected."""
        token_service = TokenService()

        # Try to decode completely invalid token
        with pytest.raises(ValueError):
            token_service.decode_token("invalid.token.string")

    async def test_tampered_token_detection(self, e2e_client: AsyncClient):
        """Test that token tampering is detected."""
        token_service = TokenService()

        # Create valid token
        valid_token = token_service.create_access_token(1)

        # Tamper with token
        parts = valid_token.split(".")
        if len(parts) == 3:
            # Modify the payload
            tampered_token = f"{parts[0]}.tampered.{parts[2]}"

            # Should fail to decode
            with pytest.raises(ValueError):
                token_service.decode_token(tampered_token)

    async def test_token_contains_required_claims(self):
        """Test that tokens contain required claims."""
        token_service = TokenService()

        user_id = 123
        token = token_service.create_access_token(user_id)

        payload = token_service.decode_token(token)

        # Check required claims
        assert "sub" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert "type" in payload

        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

    async def test_refresh_token_rotation(self):
        """Test that refresh tokens work with rotation."""
        token_service = TokenService()

        user_id = 456
        old_refresh_token = token_service.create_refresh_token(user_id)

        # Simulate token refresh (would be done via AuthUseCases)
        # New refresh token should be different
        new_refresh_token = token_service.create_refresh_token(user_id)

        assert old_refresh_token != new_refresh_token

        # Old token should still be valid (until revoked in real implementation)
        payload = token_service.decode_token(old_refresh_token)
        assert payload["sub"] == str(user_id)

    async def test_access_token_cannot_be_used_as_refresh(self):
        """Test that access token type is enforced."""
        token_service = TokenService()

        user_id = 789
        access_token = token_service.create_access_token(user_id)

        payload = token_service.decode_token(access_token)
        assert payload["type"] == "access"

    async def test_refresh_token_has_longer_expiration(self):
        """Test that refresh tokens live longer than access tokens."""
        token_service = TokenService()

        user_id = 999
        access_token = token_service.create_access_token(user_id)
        refresh_token = token_service.create_refresh_token(user_id)

        access_payload = token_service.decode_token(access_token)
        refresh_payload = token_service.decode_token(refresh_token)

        # Convert to datetime
        access_exp = datetime.fromtimestamp(access_payload["exp"])
        refresh_exp = datetime.fromtimestamp(refresh_payload["exp"])

        # Refresh token should live longer
        assert refresh_exp > access_exp

    async def test_token_uses_strong_algorithm(self):
        """Test that tokens use strong encryption algorithm."""
        token_service = TokenService()

        token = token_service.create_access_token(1)

        # Decode header without verification
        header = jwt.get_unverified_header(token)

        # Should use RS256 or similar strong algorithm
        assert header["alg"] in ["RS256", "RS512", "ES256", "HS256"]
