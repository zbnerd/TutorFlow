"""Auth DTOs for request/response handling."""
from pydantic import BaseModel, EmailStr, Field


class KakaoLoginRequest(BaseModel):
    """Kakao login request."""

    code: str = Field(..., description="Authorization code from Kakao OAuth")


class TokenRefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str = Field(..., description="JWT refresh token")


class AuthResponse(BaseModel):
    """Authentication response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    email: str | None
    name: str
    role: str


class UserInfoResponse(BaseModel):
    """User info response."""

    id: int
    email: str | None
    name: str
    role: str
    phone: str | None
    profile_image_url: str | None
    is_active: bool
