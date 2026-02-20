"""API v1 route handlers."""
from fastapi import APIRouter

from api.v1.routes import auth, attendance, bookings, payments, reviews, webhooks, settlements

api_router = APIRouter()

# Include route modules
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(settlements.router, prefix="/settlements", tags=["settlements"])


@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}
