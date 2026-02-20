"""User repository implementation."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import User, UserRole
from domain.ports import UserRepositoryPort
from infrastructure.persistence.models import UserModel
from infrastructure.persistence.repositories.audit_log_repository import AuditLogRepository


class UserRepository(UserRepositoryPort):
    """SQLAlchemy implementation of UserRepositoryPort."""

    def __init__(self, session: AsyncSession, audit_repo: Optional[AuditLogRepository] = None):
        """Initialize repository with database session and optional audit repository."""
        self.session = session
        self.audit_repo = audit_repo

    async def save(
        self,
        user: User,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> User:
        """Save user to database (create or update)."""
        if user.id is None:
            # Create new user
            new_values = {
                "email": user.email,
                "name": user.name,
                "phone": user.phone,
                "role": user.role.value if isinstance(user.role, UserRole) else user.role,
                "oauth_provider": user.oauth_provider,
                "oauth_id": user.oauth_id,
                "profile_image_url": user.profile_image_url,
                "is_active": user.is_active,
            }
            db_user = UserModel.from_entity(user)
            self.session.add(db_user)
            await self.session.flush()
            await self.session.refresh(db_user)

            # Log creation
            if self.audit_repo:
                await self.audit_repo.log_change(
                    entity_type="user",
                    entity_id=db_user.id,
                    action="create",
                    old_value=None,
                    new_value=new_values,
                    actor_id=actor_id,
                    ip_address=ip_address,
                )

            return db_user.to_entity()
        else:
            # Update existing user
            result = await self.session.execute(select(UserModel).where(UserModel.id == user.id))
            db_user = result.scalar_one_or_none()
            if db_user:
                # Capture old values for audit
                old_values = {
                    "email": db_user.email,
                    "name": db_user.name,
                    "phone": db_user.phone,
                    "role": db_user.role.value if isinstance(db_user.role, UserRole) else db_user.role,
                    "profile_image_url": db_user.profile_image_url,
                    "is_active": db_user.is_active,
                    "is_verified": db_user.is_verified,
                }

                db_user.email = user.email
                db_user.name = user.name
                db_user.phone = user.phone
                db_user.role = user.role
                db_user.profile_image_url = user.profile_image_url
                db_user.is_active = user.is_active
                db_user.is_verified = user.is_verified
                await self.session.flush()
                await self.session.refresh(db_user)

                # Capture new values for audit
                new_values = {
                    "email": user.email,
                    "name": user.name,
                    "phone": user.phone,
                    "role": user.role.value if isinstance(user.role, UserRole) else user.role,
                    "profile_image_url": user.profile_image_url,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                }

                # Log update if something changed
                if self.audit_repo and old_values != new_values:
                    await self.audit_repo.log_change(
                        entity_type="user",
                        entity_id=db_user.id,
                        action="update",
                        old_value=old_values,
                        new_value=new_values,
                        actor_id=actor_id,
                        ip_address=ip_address,
                    )

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

    async def update_role(
        self,
        user_id: int,
        new_role: UserRole,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[User]:
        """Update user role with audit logging."""
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        db_user = result.scalar_one_or_none()

        if not db_user:
            return None

        old_role = db_user.role
        db_user.role = new_role
        await self.session.flush()
        await self.session.refresh(db_user)

        # Log role change
        if self.audit_repo and old_role != new_role:
            await self.audit_repo.log_change(
                entity_type="user",
                entity_id=user_id,
                action="role_change",
                old_value={"role": old_role.value if isinstance(old_role, UserRole) else old_role},
                new_value={"role": new_role.value if isinstance(new_role, UserRole) else new_role},
                actor_id=actor_id,
                ip_address=ip_address,
            )

        return db_user.to_entity()
