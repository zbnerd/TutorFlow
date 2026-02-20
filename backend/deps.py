"""Dependency injection for FastAPI routes."""
from infrastructure.database import get_db

# Re-export commonly used dependencies
__all__ = ["get_db"]
