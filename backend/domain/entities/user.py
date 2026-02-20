"""User domain entity."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User role enumeration."""

    TUTOR = "tutor"
    STUDENT = "student"
    ADMIN = "admin"


class User(BaseModel):
    """User domain entity."""

    id: int | None = None
    email: EmailStr
    name: str
    role: UserRole
    kakao_id: str | None = None
    phone: str | None = None
    profile_image_url: str | None = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        from_attributes = True


class UserCreate(BaseModel):
    """User creation DTO."""

    email: EmailStr
    name: str
    role: UserRole
    kakao_id: str | None = None
    phone: str | None = None
    profile_image_url: str | None = None


class UserUpdate(BaseModel):
    """User update DTO."""

    email: EmailStr | None = None
    name: str | None = None
    phone: str | None = None
    profile_image_url: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
