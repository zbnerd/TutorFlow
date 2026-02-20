"""Repository implementations for domain entities."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import User
from domain.ports import UserRepositoryPort
from infrastructure.persistence.models import UserModel


class UserRepository(UserRepositoryPort):
    """SQLAlchemy implementation of UserRepositoryPort."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def save(self, user: User) -> User:
        """Save user to database (create or update)."""
        if user.id is None:
            # Create new user
            db_user = UserModel.from_entity(user)
            self.session.add(db_user)
            await self.session.flush()
            await self.session.refresh(db_user)
            return db_user.to_entity()
        else:
            # Update existing user
            result = await self.session.execute(select(UserModel).where(UserModel.id == user.id))
            db_user = result.scalar_one_or_none()
            if db_user:
                db_user.email = user.email
                db_user.name = user.name
                db_user.phone = user.phone
                db_user.role = user.role
                db_user.profile_image_url = user.profile_image_url
                db_user.is_active = user.is_active
                db_user.is_verified = user.is_verified
                await self.session.flush()
                await self.session.refresh(db_user)
                return db_user.to_entity()
            return user

    async def find_by_id(self, user_id: int) -> Optional[User]:
        """Find user by ID."""
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        db_user = result.scalar_one_or_none()
        return db_user.to_entity() if db_user else None

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        result = await self.session.execute(select(UserModel).where(UserModel.email == email))
        db_user = result.scalar_one_or_none()
        return db_user.to_entity() if db_user else None

    async def find_by_oauth_id(self, provider: str, oauth_id: str) -> Optional[User]:
        """Find user by OAuth provider ID."""
        result = await self.session.execute(
            select(UserModel).where(
                UserModel.oauth_provider == provider,
                UserModel.oauth_id == oauth_id,
            )
        )
        db_user = result.scalar_one_or_none()
        return db_user.to_entity() if db_user else None
