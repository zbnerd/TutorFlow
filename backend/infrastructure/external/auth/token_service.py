"""JWT token service implementation."""
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from config import settings


class TokenService:
    """JWT token service implementation of TokenPort."""

    def __init__(self):
        """Initialize token service."""
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(self, data: dict[str, Any]) -> str:
        """
        Create JWT access token.

        Args:
            data: Payload data to encode (typically user_id, email, etc.)

        Returns:
            JWT access token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({
            "exp": expire,
            "type": "access",
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: dict[str, Any]) -> str:
        """
        Create JWT refresh token.

        Args:
            data: Payload data to encode (typically user_id)

        Returns:
            JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({
            "exp": expire,
            "type": "refresh",
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict[str, Any]:
        """
        Decode and verify JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            JWTError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            raise JWTError(f"Invalid token: {str(e)}")

    def create_token_pair(self, user_id: int, email: str, role: str) -> dict[str, str]:
        """
        Create both access and refresh tokens for a user.

        Args:
            user_id: User's database ID
            email: User's email
            role: User's role (tutor, student, admin)

        Returns:
            Dict with access_token and refresh_token
        """
        token_data = {
            "sub": str(user_id),
            "email": email,
            "role": role,
        }

        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token({"sub": str(user_id)})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
