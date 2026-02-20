"""Authentication routes for Kakao OAuth and token management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.routes.dependencies import get_current_user
from application.dto.auth import AuthResponse, TokenRefreshRequest, UserInfoResponse, KakaoLoginRequest
from application.use_cases.auth import AuthUseCases
from domain.entities import User
from infrastructure.external.auth import KakaoOAuthAdapter, TokenService
from infrastructure.persistence.repositories import UserRepository
from infrastructure.database import get_db
from typing import Annotated


router = APIRouter()


@router.post("/kakao", response_model=AuthResponse)
async def kakao_login(
    request: KakaoLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Kakao OAuth login callback.

    Exchanges authorization code for access token, retrieves user info,
    creates/updates user, and returns JWT tokens.

    Args:
        code: Authorization code from Kakao OAuth callback

    Returns:
        AuthResponse with access_token, refresh_token, and user info

    Raises:
        HTTPException 400: If OAuth exchange fails or user info is invalid
    """
    user_repo = UserRepository(db)
    oauth_adapter = KakaoOAuthAdapter()
    token_service = TokenService()

    auth_use_cases = AuthUseCases(
        user_repo=user_repo,
        oauth_adapter=oauth_adapter,
        token_service=token_service,
    )

    try:
        user, token_pair = await auth_use_cases.kakao_login(request.code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth login failed: {str(e)}",
        )

    return AuthResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        user_id=user.id,
        email=user.email,
        name=user.name or "",
        role=user.role.value,
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_tokens(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    Validates the refresh token and returns a new token pair
    with token rotation (new refresh token).

    Args:
        request: TokenRefreshRequest containing refresh_token

    Returns:
        AuthResponse with new access_token and refresh_token

    Raises:
        HTTPException 401: If refresh token is invalid or expired
        HTTPException 404: If user not found
    """
    user_repo = UserRepository(db)
    oauth_adapter = KakaoOAuthAdapter()
    token_service = TokenService()

    auth_use_cases = AuthUseCases(
        user_repo=user_repo,
        oauth_adapter=oauth_adapter,
        token_service=token_service,
    )

    try:
        token_pair = await auth_use_cases.refresh_tokens(request.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    # Get user info for response
    payload = token_service.decode_token(token_pair.access_token)
    user_id = int(payload.get("sub", 0))
    user = await auth_use_cases.get_current_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return AuthResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        user_id=user.id,
        email=user.email,
        name=user.name or "",
        role=user.role.value,
    )


@router.get("/me", response_model=UserInfoResponse)
async def get_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get current user info from access token.

    Requires valid access token in Authorization header.

    Returns:
        UserInfoResponse with current user details

    Raises:
        HTTPException 401: If token is invalid or expired
        HTTPException 404: If user not found
    """
    return UserInfoResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name or "",
        role=current_user.role.value if current_user.role else "student",
        phone=current_user.phone,
        profile_image_url=current_user.profile_image_url,
        is_active=current_user.is_active,
    )
