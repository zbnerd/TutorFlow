"""Health check endpoints with detailed status monitoring."""
from datetime import datetime
from typing import Any
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from infrastructure.database import get_db
from config import settings


router = APIRouter()


async def check_database(db: AsyncSession) -> dict[str, Any]:
    """Check database connectivity."""
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        return {
            "status": "healthy",
            "latency_ms": 0,  # Could measure actual latency
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def check_external_services() -> dict[str, Any]:
    """Check external service availability.

    NOTE: This is a template. Actual implementation would check:
    - Kakao OAuth API
    - Toss Payments API
    - Kakao Alimtalk API
    """
    # TODO: Implement actual external service health checks
    return {
        "kakao_oauth": {"status": "unknown", "message": "Not yet implemented"},
        "toss_payments": {"status": "unknown", "message": "Not yet implemented"},
        "kakao_alimtalk": {"status": "unknown", "message": "Not yet implemented"},
    }


async def get_system_info() -> dict[str, Any]:
    """Get system information."""
    import psutil
    import platform

    return {
        "hostname": platform.node(),
        "system": platform.system(),
        "python_version": platform.python_version(),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage_percent": psutil.disk_usage("/").percent,
    }


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with all component statuses."""
    db_health = await check_database(db)
    external_health = await check_external_services()
    system_info = await get_system_info()

    # Determine overall status
    all_healthy = (
        db_health["status"] == "healthy"
        and all(
            s.get("status") in ["healthy", "unknown"]
            for s in external_health.values()
        )
    )

    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "components": {
            "database": db_health,
            "external_services": external_health,
        },
        "system": system_info,
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check for Kubernetes/Docker deployments."""
    db_health = await check_database(db)

    if db_health["status"] == "healthy":
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
        }
    else:
        return {
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "Database not available",
        }


@router.get("/health/live")
async def liveness_check():
    """Liveness check for Kubernetes/Docker deployments.

    If this endpoint returns non-200, the container will be restarted.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/db")
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """Check database health specifically."""
    health = await check_database(db)

    status_code = 200 if health["status"] == "healthy" else 503
    return {
        "database": health,
        "timestamp": datetime.utcnow().isoformat(),
    }
