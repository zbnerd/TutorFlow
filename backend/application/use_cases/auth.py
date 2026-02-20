"""Auth use cases for login and token management."""
from dataclasses import dataclass
from typing import Optional

from domain.entities import User, UserRole
from domain.ports import UserRepositoryPort
from domain.value_objects import OAuthUserInfo, TokenPair
from infrastructure.external.auth import KakaoOAuthAdapter, TokenService


@dataclass
class AuthUseCases:
    """Authentication use cases."""

    user_repo: UserRepositoryPort
    oauth_adapter: KakaoOAuthAdapter
    token_service: TokenService

    async def kakao_login(self, code: str) -> tuple[User, TokenPair]:
        """
        Handle Kakao OAuth login flow.

        1. Exchange authorization code for access token
        2. Get user info from Kakao
        3. Find or create user in database
        4. Generate JWT tokens

        Args:
            code: Authorization code from Kakao OAuth callback

        Returns:
            Tuple of (User entity, TokenPair with access and refresh tokens)

        Raises:
            httpx.HTTPError: If OAuth communication fails
            ValueError: If user info is invalid
        """
        # Exchange code for access token
        token_response = await self.oauth_adapter.exchange_code_for_token(code)
        access_token = token_response.get("access_token")

        if not access_token:
            raise ValueError("Failed to obtain access token from Kakao")

        # Get user info from Kakao
        user_info = await self.oauth_adapter.get_user_info(access_token)

        # Extract user data
        kakao_id = str(user_info.get("id", ""))
        properties = user_info.get("properties", {})
        kakao_account = user_info.get("kakao_account", {})

        email = kakao_account.get("email")
        name = properties.get("nickname", "")
        profile_image_url = properties.get("profile_image_url")
        phone = kakao_account.get("phone_number")

        # Find existing user or create new one
        user = await self.user_repo.find_by_oauth_id("kakao", kakao_id)

        if not user:
            # Create new user
            # Determine role based on email or default to student
            # In production, this might go through a registration flow
            user = User(
                email=email,
                name=name,
                role=UserRole.STUDENT,  # Default role for new users
                oauth_provider="kakao",
                oauth_id=kakao_id,
                phone=phone,
                profile_image_url=profile_image_url,
                is_active=True,
            )
            user = await self.user_repo.save(user)
        else:
            # Update user info
            user.name = name
            user.profile_image_url = profile_image_url
            if email:
                user.email = email
            if phone:
                user.phone = phone
            user = await self.user_repo.save(user)

        # Generate JWT tokens
        token_pair = self.token_service.create_token_pair(
            user_id=user.id,
            email=user.email or "",
            role=user.role.value,
        )

        return user, TokenPair(
            access_token=token_pair["access_token"],
            refresh_token=token_pair["refresh_token"],
            token_type=token_pair["token_type"],
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenPair:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid JWT refresh token

        Returns:
            New TokenPair with new access and refresh tokens

        Raises:
            JWTError: If refresh token is invalid or expired
            ValueError: If user not found
        """
        # Decode refresh token
        payload = self.token_service.decode_token(refresh_token)

        # Verify it's a refresh token
        token_type = payload.get("type")
        if token_type != "refresh":
            raise ValueError("Invalid token type")

        # Get user ID from token
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise ValueError("Invalid token payload")

        user_id = int(user_id_str)

        # Get user from database
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if not user.is_active:
            raise ValueError("User is not active")

        # Generate new token pair (token rotation)
        token_pair = self.token_service.create_token_pair(
            user_id=user.id,
            email=user.email or "",
            role=user.role.value,
        )

        return TokenPair(
            access_token=token_pair["access_token"],
            refresh_token=token_pair["refresh_token"],
            token_type=token_pair["token_type"],
        )

    async def get_current_user(self, user_id: int) -> Optional[User]:
        """
        Get current user by ID.

        Args:
            user_id: User's database ID

        Returns:
            User entity or None if not found
        """
        return await self.user_repo.find_by_id(user_id)
