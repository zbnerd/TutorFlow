"""AvailableSlot repository implementation."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import AvailableSlot
from domain.ports import AvailableSlotRepositoryPort
from infrastructure.persistence.models import AvailableSlotModel
from infrastructure.persistence.repositories.audit_log_repository import AuditLogRepository


class AvailableSlotRepository(AvailableSlotRepositoryPort):
    """SQLAlchemy implementation of AvailableSlotRepositoryPort."""

    def __init__(self, session: AsyncSession, audit_repo: Optional[AuditLogRepository] = None):
        """Initialize repository with database session and optional audit repository."""
        self.session = session
        self.audit_repo = audit_repo

    async def get_tutor_slots(
        self,
        tutor_id: int,
        active_only: bool = True,
    ) -> List[AvailableSlot]:
        """Get all available slots for a tutor."""
        query = select(AvailableSlotModel).where(AvailableSlotModel.tutor_id == tutor_id)

        if active_only:
            query = query.where(AvailableSlotModel.is_active == True)

        query = query.order_by(
            AvailableSlotModel.day_of_week,
            AvailableSlotModel.start_time
        )

        result = await self.session.execute(query)
        db_slots = result.scalars().all()
        return [self._to_entity(slot) for slot in db_slots]

    async def create_slot(
        self,
        tutor_id: int,
        day_of_week: int,
        start_time: str,
        end_time: str,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> AvailableSlot:
        """Create a new available slot."""
        new_values = {
            "tutor_id": tutor_id,
            "day_of_week": day_of_week,
            "start_time": start_time,
            "end_time": end_time,
            "is_active": True,
        }

        db_slot = AvailableSlotModel(
            tutor_id=tutor_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            is_active=True,
        )

        self.session.add(db_slot)
        await self.session.flush()
        await self.session.refresh(db_slot)

        # Log creation
        if self.audit_repo:
            await self.audit_repo.log_change(
                entity_type="available_slot",
                entity_id=db_slot.id,
                action="create",
                old_value=None,
                new_value=new_values,
                actor_id=actor_id,
                ip_address=ip_address,
            )

        return self._to_entity(db_slot)

    async def update_slot(
        self,
        slot_id: int,
        day_of_week: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        is_active: Optional[bool] = None,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[AvailableSlot]:
        """Update an available slot."""
        result = await self.session.execute(
            select(AvailableSlotModel).where(AvailableSlotModel.id == slot_id)
        )
        db_slot = result.scalar_one_or_none()

        if not db_slot:
            return None

        # Capture old values for audit
        old_values = {
            "day_of_week": db_slot.day_of_week,
            "start_time": db_slot.start_time,
            "end_time": db_slot.end_time,
            "is_active": db_slot.is_active,
        }

        # Update fields if provided
        if day_of_week is not None:
            db_slot.day_of_week = day_of_week
        if start_time is not None:
            db_slot.start_time = start_time
        if end_time is not None:
            db_slot.end_time = end_time
        if is_active is not None:
            db_slot.is_active = is_active

        await self.session.flush()
        await self.session.refresh(db_slot)

        # Capture new values for audit
        new_values = {
            "day_of_week": db_slot.day_of_week,
            "start_time": db_slot.start_time,
            "end_time": db_slot.end_time,
            "is_active": db_slot.is_active,
        }

        # Log update if something changed
        if self.audit_repo and old_values != new_values:
            await self.audit_repo.log_change(
                entity_type="available_slot",
                entity_id=slot_id,
                action="update",
                old_value=old_values,
                new_value=new_values,
                actor_id=actor_id,
                ip_address=ip_address,
            )

        return self._to_entity(db_slot)

    async def delete_slot(
        self,
        slot_id: int,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> bool:
        """Delete an available slot."""
        result = await self.session.execute(
            select(AvailableSlotModel).where(AvailableSlotModel.id == slot_id)
        )
        db_slot = result.scalar_one_or_none()

        if not db_slot:
            return False

        # Capture old values for audit
        old_values = {
            "tutor_id": db_slot.tutor_id,
            "day_of_week": db_slot.day_of_week,
            "start_time": db_slot.start_time,
            "end_time": db_slot.end_time,
            "is_active": db_slot.is_active,
        }

        await self.session.delete(db_slot)
        await self.session.flush()

        # Log deletion
        if self.audit_repo:
            await self.audit_repo.log_change(
                entity_type="available_slot",
                entity_id=slot_id,
                action="delete",
                old_value=old_values,
                new_value=None,
                actor_id=actor_id,
                ip_address=ip_address,
            )

        return True

    async def check_availability(
        self,
        tutor_id: int,
        day_of_week: int,
        time: str,
    ) -> bool:
        """Check if tutor is available at a specific time."""
        result = await self.session.execute(
            select(AvailableSlotModel).where(
                and_(
                    AvailableSlotModel.tutor_id == tutor_id,
                    AvailableSlotModel.day_of_week == day_of_week,
                    AvailableSlotModel.is_active == True,
                    AvailableSlotModel.start_time <= time,
                    AvailableSlotModel.end_time > time,
                )
            )
        )

        db_slot = result.scalar_one_or_none()
        return db_slot is not None

    async def get_slot_by_id(self, slot_id: int) -> Optional[AvailableSlot]:
        """Get a slot by ID."""
        result = await self.session.execute(
            select(AvailableSlotModel).where(AvailableSlotModel.id == slot_id)
        )
        db_slot = result.scalar_one_or_none()
        return self._to_entity(db_slot) if db_slot else None

    def _to_entity(self, db_slot: AvailableSlotModel) -> AvailableSlot:
        """Convert ORM model to domain entity."""
        return AvailableSlot(
            id=db_slot.id,
            tutor_id=db_slot.tutor_id,
            day_of_week=db_slot.day_of_week,
            start_time=db_slot.start_time,
            end_time=db_slot.end_time,
            is_active=db_slot.is_active,
        )
