"""Audit logging port for tracking all state changes."""
from typing import Protocol, runtime_checkable, Optional, Dict, Any

@runtime_checkable
class AuditPort(Protocol):
    """Audit logging repository interface."""

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
        """Log a state change for an entity.

        Args:
            entity_type: Type of entity (e.g., "booking", "payment", "review")
            entity_id: ID of the entity being changed
            action: Action performed (e.g., "create", "update", "delete")
            old_value: Previous state as dictionary (None for create actions)
            new_value: New state as dictionary (None for delete actions)
            actor_id: ID of the user who made the change
            ip_address: IP address of the requester
        """

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: int,
    ) -> list[Dict[str, Any]]:
        """Get audit history for an entity.

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity

        Returns:
            List of audit log entries for this entity, ordered by created_at desc
        """
