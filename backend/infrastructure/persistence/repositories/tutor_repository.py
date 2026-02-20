"""Tutor repository implementation."""
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Tutor, Money, NoShowPolicy
from domain.ports import TutorRepositoryPort
from infrastructure.persistence.models import TutorModel
from infrastructure.persistence.repositories.audit_log_repository import AuditLogRepository


class TutorRepository(TutorRepositoryPort):
    """SQLAlchemy implementation of TutorRepositoryPort."""

    def __init__(self, session: AsyncSession, audit_repo: Optional[AuditLogRepository] = None):
        """Initialize repository with database session and optional audit repository."""
        self.session = session
        self.audit_repo = audit_repo

    async def save(
        self,
        tutor: Tutor,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Tutor:
        """Save tutor to database (create or update)."""
        if tutor.id is None:
            # Create new tutor
            new_values = {
                "user_id": tutor.user_id,
                "bio": tutor.bio,
                "subjects": tutor.subjects,
                "hourly_rate": tutor.hourly_rate.amount_krw if tutor.hourly_rate else None,
                "no_show_policy": tutor.no_show_policy.value if isinstance(tutor.no_show_policy, NoShowPolicy) else tutor.no_show_policy,
                "is_approved": tutor.is_approved,
                "bank_name": tutor.bank_name,
                "bank_account": tutor.bank_account,
                "bank_holder": tutor.bank_holder,
            }
            db_tutor = TutorModel(
                user_id=tutor.user_id,
                bio=tutor.bio,
                subjects=tutor.subjects,
                hourly_rate=tutor.hourly_rate.amount_krw if tutor.hourly_rate else None,
                no_show_policy=tutor.no_show_policy,
                is_approved=tutor.is_approved,
                bank_name=tutor.bank_name,
                bank_account=tutor.bank_account,
                bank_holder=tutor.bank_holder,
            )
            self.session.add(db_tutor)
            await self.session.flush()
            await self.session.refresh(db_tutor)

            # Log creation
            if self.audit_repo:
                await self.audit_repo.log_change(
                    entity_type="tutor",
                    entity_id=db_tutor.id,
                    action="create",
                    old_value=None,
                    new_value=new_values,
                    actor_id=actor_id,
                    ip_address=ip_address,
                )

            return self._to_entity(db_tutor)
        else:
            # Update existing tutor
            result = await self.session.execute(
                select(TutorModel).where(TutorModel.id == tutor.id)
            )
            db_tutor = result.scalar_one_or_none()
            if db_tutor:
                # Capture old values for audit
                old_values = {
                    "bio": db_tutor.bio,
                    "subjects": db_tutor.subjects,
                    "hourly_rate": db_tutor.hourly_rate,
                    "no_show_policy": db_tutor.no_show_policy.value if isinstance(db_tutor.no_show_policy, NoShowPolicy) else db_tutor.no_show_policy,
                    "is_approved": db_tutor.is_approved,
                    "bank_name": db_tutor.bank_name,
                    "bank_account": db_tutor.bank_account,
                    "bank_holder": db_tutor.bank_holder,
                }

                db_tutor.bio = tutor.bio
                db_tutor.subjects = tutor.subjects
                db_tutor.hourly_rate = tutor.hourly_rate.amount_krw if tutor.hourly_rate else None
                db_tutor.no_show_policy = tutor.no_show_policy
                db_tutor.is_approved = tutor.is_approved
                db_tutor.bank_name = tutor.bank_name
                db_tutor.bank_account = tutor.bank_account
                db_tutor.bank_holder = tutor.bank_holder
                await self.session.flush()
                await self.session.refresh(db_tutor)

                # Capture new values for audit
                new_values = {
                    "bio": tutor.bio,
                    "subjects": tutor.subjects,
                    "hourly_rate": tutor.hourly_rate.amount_krw if tutor.hourly_rate else None,
                    "no_show_policy": tutor.no_show_policy.value if isinstance(tutor.no_show_policy, NoShowPolicy) else tutor.no_show_policy,
                    "is_approved": tutor.is_approved,
                    "bank_name": tutor.bank_name,
                    "bank_account": tutor.bank_account,
                    "bank_holder": tutor.bank_holder,
                }

                # Log update if something changed
                if self.audit_repo and old_values != new_values:
                    await self.audit_repo.log_change(
                        entity_type="tutor",
                        entity_id=db_tutor.id,
                        action="update",
                        old_value=old_values,
                        new_value=new_values,
                        actor_id=actor_id,
                        ip_address=ip_address,
                    )

                return self._to_entity(db_tutor)
            return tutor

    async def find_by_id(self, tutor_id: int) -> Optional[Tutor]:
        """Find tutor by ID."""
        result = await self.session.execute(
            select(TutorModel).where(TutorModel.id == tutor_id)
        )
        db_tutor = result.scalar_one_or_none()
        return self._to_entity(db_tutor) if db_tutor else None

    async def find_by_user_id(self, user_id: int) -> Optional[Tutor]:
        """Find tutor profile by user ID."""
        result = await self.session.execute(
            select(TutorModel).where(TutorModel.user_id == user_id)
        )
        db_tutor = result.scalar_one_or_none()
        return self._to_entity(db_tutor) if db_tutor else None

    async def list_approved(
        self,
        offset: int = 0,
        limit: int = 20,
        subject: Optional[str] = None,
    ) -> List[Tutor]:
        """List approved tutors with optional filtering."""
        query = select(TutorModel).where(TutorModel.is_approved == True)

        if subject:
            # Filter by subject (JSON contains)
            query = query.where(TutorModel.subjects.contains([subject]))

        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        db_tutors = result.scalars().all()
        return [self._to_entity(t) for t in db_tutors]

    async def update_approval_status(
        self,
        tutor_id: int,
        is_approved: bool,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[Tutor]:
        """Update tutor approval status with audit logging."""
        result = await self.session.execute(
            select(TutorModel).where(TutorModel.id == tutor_id)
        )
        db_tutor = result.scalar_one_or_none()

        if not db_tutor:
            return None

        old_status = db_tutor.is_approved
        db_tutor.is_approved = is_approved
        await self.session.flush()
        await self.session.refresh(db_tutor)

        # Log approval status change
        if self.audit_repo and old_status != is_approved:
            await self.audit_repo.log_change(
                entity_type="tutor",
                entity_id=tutor_id,
                action="approval_change",
                old_value={"is_approved": old_status},
                new_value={"is_approved": is_approved},
                actor_id=actor_id,
                ip_address=ip_address,
            )

        return self._to_entity(db_tutor)

    def _to_entity(self, db_tutor: TutorModel) -> Tutor:
        """Convert ORM model to domain entity."""
        return Tutor(
            id=db_tutor.id,
            user_id=db_tutor.user_id,
            bio=db_tutor.bio,
            subjects=db_tutor.subjects,
            hourly_rate=Money(db_tutor.hourly_rate) if db_tutor.hourly_rate else None,
            no_show_policy=db_tutor.no_show_policy,
            is_approved=db_tutor.is_approved,
            bank_name=db_tutor.bank_name,
            bank_account=db_tutor.bank_account,
            bank_holder=db_tutor.bank_holder,
            created_at=db_tutor.created_at,
            updated_at=db_tutor.updated_at,
        )
