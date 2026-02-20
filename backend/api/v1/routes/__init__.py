"""API v1 route handlers."""
from fastapi import APIRouter

from api.v1.routes import auth

api_router = APIRouter()

# Include route modules
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Future routes
# api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
# api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
# api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])


@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}
