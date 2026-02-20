"""Audit log repository implementation."""
from datetime import datetime
from typing import Optional, Dict, Any
import json

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import AuditLog
from domain.ports import AuditPort
from infrastructure.persistence.models import AuditLogModel


class AuditLogRepository(AuditPort):
    """SQLAlchemy implementation of AuditPort."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def log_change(
        self,
        entity_type: str,
        entity_id: int,
        action: str,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log a state change for an entity."""
        db_log = AuditLogModel(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
            actor_id=actor_id,
            ip_address=ip_address,
            created_at=datetime.utcnow(),
        )
        self.session.add(db_log)
        await self.session.flush()

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: int,
    ) -> list[Dict[str, Any]]:
        """Get audit history for an entity."""
        result = await self.session.execute(
            select(AuditLogModel)
            .where(
                and_(
                    AuditLogModel.entity_type == entity_type,
                    AuditLogModel.entity_id == entity_id,
                )
            )
            .order_by(AuditLogModel.created_at.desc())
        )
        db_logs = result.scalars().all()

        return [
            {
                "id": log.id,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "action": log.action,
                "old_value": json.loads(log.old_value) if log.old_value else None,
                "new_value": json.loads(log.new_value) if log.new_value else None,
                "actor_id": log.actor_id,
                "ip_address": log.ip_address,
                "created_at": log.created_at,
            }
            for log in db_logs
        ]
