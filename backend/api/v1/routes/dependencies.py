"""API dependencies for authentication and database access."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from domain.entities import UserRole, User
from infrastructure.database import get_db
from infrastructure.external.auth.token_service import TokenService
from infrastructure.persistence.repository_factory import RepositoryFactory
from infrastructure.persistence.repositories.user_repository import UserRepository


# Authentication dependencies
security = HTTPBearer()


security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get current authenticated user from JWT token.

    Validates the access token and returns the user entity.

    Args:
        credentials: HTTP Bearer token credentials
        db: Database session

    Returns:
        User entity from database

    Raises:
        HTTPException 401: If token is invalid, expired, or user not found
    """
    token = credentials.credentials
    token_service = TokenService()

    try:
        payload = token_service.decode_token(token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate token type
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user_id from token
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user_repo = UserRepository(db)
    user = await user_repo.find_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_tutor(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Verify current user is a tutor.

    Args:
        current_user: Current authenticated user

    Returns:
        User entity with tutor role

    Raises:
        HTTPException 403: If user is not a tutor
    """
    if current_user.role != UserRole.TUTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tutors can perform this action",
        )

    return current_user


async def get_current_student(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Verify current user is a student.

    Args:
        current_user: Current authenticated user

    Returns:
        User entity with student role

    Raises:
        HTTPException 403: If user is not a student
    """
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can perform this action",
        )

    return current_user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Verify current user is an admin.

    Args:
        current_user: Current authenticated user

    Returns:
        User entity with admin role

    Raises:
        HTTPException 403: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action",
        )

    return current_user


async def get_current_tutor_or_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Verify current user is a tutor or admin.

    Args:
        current_user: Current authenticated user

    Returns:
        User entity with tutor or admin role

    Raises:
        HTTPException 403: If user is not a tutor or admin
    """
    if current_user.role not in [UserRole.TUTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tutors and admins can perform this action",
        )

    return current_user


# Repository factory dependency
async def get_repository_factory(
    db: AsyncSession = Depends(get_db),
) -> RepositoryFactory:
    """
    Get repository factory with database session.

    Args:
        db: Database session

    Returns:
        RepositoryFactory instance
    """
    return RepositoryFactory(db)
