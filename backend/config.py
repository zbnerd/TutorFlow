"""Application configuration using Pydantic Settings."""
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "TutorFlow API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://tutorflow:tutorflow@localhost:5432/tutorflow"
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # JWT
    SECRET_KEY: str = Field(default="CHANGE_THIS_IN_PRODUCTION_MIN_32_CHARS!")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"])

    # Kakao OAuth
    KAKAO_CLIENT_ID: str = ""
    KAKAO_CLIENT_SECRET: str = ""
    KAKAO_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/kakao/callback"

    # Toss Payments
    TOSS_PAYMENTS_API_KEY: str = ""
    TOSS_PAYMENTS_SECRET_KEY: str = ""
    TOSS_PAYMENTS_API_URL: str = "https://api.tosspayments.com/v1"
    TOSS_PAYMENTS_FEE_RATE: float = 0.05  # 5% platform fee

    # Kakao Alimtalk
    KAKAO_ALIMTalk_API_KEY: str = ""
    KAKAO_ALIMTalk_SENDER: str = "TutorFlow"

    # Alimtalk Template Codes
    KAKAO_ALIMTalk_TEMPLATE_SESSION_REMINDER: str = ""  # 24-hour before session reminder
    KAKAO_ALIMTalk_TEMPLATE_ATTENDANCE_CHECK: str = ""  # Attendance check reminder for tutors

    # Batch Job Schedule (Cron format)
    BATCH_AUTO_ATTENDANCE_SCHEDULE: str = "59 23 * * *"  # Daily at 23:59
    BATCH_ATTENDANCE_REMINDER_SCHEDULE: str = "0 12 * * *"  # Daily at 12:00
    BATCH_SESSION_REMINDER_SCHEDULE: str = "0 9 * * *"  # Daily at 09:00 (24h before sessions)

    # Batch Job Settings
    BATCH_JOBS_ENABLED: bool = True
    BATCH_TIMEZONE: str = "Asia/Seoul"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key is not default in production."""
        import os

        if (
            v == "CHANGE_THIS_IN_PRODUCTION_MIN_32_CHARS!"
            and os.getenv("ENVIRONMENT") == "production"
        ):
            raise ValueError("SECRET_KEY must be set in production")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
