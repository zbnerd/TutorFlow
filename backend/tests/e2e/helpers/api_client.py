"""Helper module for API client utilities in E2E tests."""
from datetime import date, timedelta
from typing import Any
from httpx import AsyncClient


class APIClient:
    """Helper class for making API requests in E2E tests."""

    def __init__(self, client: AsyncClient):
        """Initialize with an httpx async client."""
        self.client = client

    async def create_booking(
        self,
        tutor_id: int,
        slots: list[dict],
        notes: str = "",
    ) -> dict[str, Any]:
        """Create a booking request."""
        booking_request = {
            "tutor_id": tutor_id,
            "slots": slots,
            "notes": notes,
        }
        response = await self.client.post("/bookings", json=booking_request)
        response.raise_for_status()
        return response.json()

    async def approve_booking(self, booking_id: int) -> dict[str, Any]:
        """Approve a booking."""
        response = await self.client.patch(f"/bookings/{booking_id}/approve")
        response.raise_for_status()
        return response.json()

    async def reject_booking(self, booking_id: int, reason: str = "") -> dict[str, Any]:
        """Reject a booking."""
        response = await self.client.patch(
            f"/bookings/{booking_id}/reject",
            json={"reason": reason}
        )
        response.raise_for_status()
        return response.json()

    async def cancel_booking(self, booking_id: int) -> dict[str, Any]:
        """Cancel a booking."""
        response = await self.client.delete(f"/bookings/{booking_id}")
        response.raise_for_status()
        return response.json()

    async def get_booking(self, booking_id: int) -> dict[str, Any]:
        """Get booking details."""
        response = await self.client.get(f"/bookings/{booking_id}")
        response.raise_for_status()
        return response.json()

    async def list_bookings(
        self,
        tutor_id: int | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        """List bookings with optional filters."""
        params = {"offset": offset, "limit": limit}
        if tutor_id:
            params["tutor_id"] = tutor_id
        if status:
            params["status"] = status

        response = await self.client.get("/bookings", params=params)
        response.raise_for_status()
        return response.json()

    async def mark_attendance(
        self,
        session_id: int,
        status: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Mark attendance for a session."""
        attendance_request = {"status": status}
        if notes:
            attendance_request["notes"] = notes

        response = await self.client.patch(
            f"/attendance/sessions/{session_id}",
            json=attendance_request
        )
        response.raise_for_status()
        return response.json()

    async def get_sessions(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Get sessions for attendance."""
        params = {"offset": offset, "limit": limit}
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        if status:
            params["status"] = status

        response = await self.client.get("/attendance/sessions", params=params)
        response.raise_for_status()
        return response.json()

    async def create_review(
        self,
        booking_id: int,
        tutor_id: int,
        student_id: int,
        overall_rating: int,
        content: str,
        kindness_rating: int | None = None,
        preparation_rating: int | None = None,
        improvement_rating: int | None = None,
        punctuality_rating: int | None = None,
        is_anonymous: bool = True,
    ) -> dict[str, Any]:
        """Create a review."""
        review_request = {
            "booking_id": booking_id,
            "tutor_id": tutor_id,
            "student_id": student_id,
            "overall_rating": overall_rating,
            "kindness_rating": kindness_rating or overall_rating,
            "preparation_rating": preparation_rating or overall_rating,
            "improvement_rating": improvement_rating or overall_rating,
            "punctuality_rating": punctuality_rating or overall_rating,
            "content": content,
            "is_anonymous": is_anonymous,
        }

        response = await self.client.post(
            "/reviews",
            params={"current_user_id": student_id},
            json=review_request
        )
        response.raise_for_status()
        return response.json()

    async def get_review(self, review_id: int) -> dict[str, Any]:
        """Get a specific review."""
        response = await self.client.get(f"/reviews/{review_id}")
        response.raise_for_status()
        return response.json()

    async def get_tutor_reviews(
        self,
        tutor_id: int,
        min_rating: float | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Get reviews for a tutor."""
        params = {"offset": offset, "limit": limit}
        if min_rating:
            params["min_rating"] = min_rating

        response = await self.client.get(
            f"/reviews/tutors/{tutor_id}/reviews",
            params=params
        )
        response.raise_for_status()
        return response.json()

    async def add_tutor_reply(
        self,
        review_id: int,
        tutor_id: int,
        reply: str,
    ) -> dict[str, Any]:
        """Add tutor reply to a review."""
        response = await self.client.post(
            f"/reviews/{review_id}/reply",
            params={"current_user_id": tutor_id},
            json={"reply": reply}
        )
        response.raise_for_status()
        return response.json()

    async def report_review(
        self,
        review_id: int,
        reporter_id: int,
        reason: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Report a review for moderation."""
        response = await self.client.post(
            f"/reviews/{review_id}/report",
            params={"current_user_id": reporter_id},
            json={"reason": reason, "description": description}
        )
        response.raise_for_status()
        return response.json()


def create_test_slots(
    days_from_now: int = 1,
    count: int = 1,
    start_time: str = "14:00",
    end_time: str = "16:00",
) -> list[dict]:
    """Create test booking slot data.

    Args:
        days_from_now: Start date offset from today
        count: Number of slots to create (weekly intervals)
        start_time: Start time for each slot
        end_time: End time for each slot

    Returns:
        List of slot dictionaries for booking requests
    """
    slots = []
    for i in range(count):
        slot_date = (date.today() + timedelta(days=days_from_now + (i * 7)))
        slots.append({
            "date": slot_date.strftime("%Y-%m-%d"),
            "start_time": start_time,
            "end_time": end_time,
        })
    return slots
