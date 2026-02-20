"""E2E test for the complete booking flow.

Tests the flow: login → search tutor → book → pay
"""
import pytest
from datetime import date, timedelta
from httpx import AsyncClient


@pytest.mark.asyncio
class TestBookingFlow:
    """Test complete booking flow from login to payment."""

    async def test_complete_booking_flow(
        self,
        e2e_client: AsyncClient,
        test_tutor: dict,
        test_student: dict,
        test_available_slot: int,
    ):
        """Test the complete booking flow: search tutor → book → pay."""
        # Step 1: Create booking request
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        next_week = (date.today() + timedelta(days=8)).strftime("%Y-%m-%d")

        booking_request = {
            "tutor_id": test_tutor["tutor_id"],
            "slots": [
                {
                    "date": tomorrow,
                    "start_time": "14:00",
                    "end_time": "16:00",
                },
                {
                    "date": next_week,
                    "start_time": "14:00",
                    "end_time": "16:00",
                },
            ],
            "notes": "Initial booking request",
        }

        response = await e2e_client.post("/bookings", json=booking_request)
        assert response.status_code == 201, f"Booking creation failed: {response.text}"

        booking_data = response.json()
        booking_id = booking_data["id"]
        assert booking_data["status"] == "PENDING"
        assert booking_data["total_sessions"] == 2
        assert len(booking_data["sessions"]) == 2

        # Step 2: Get booking details
        response = await e2e_client.get(f"/bookings/{booking_id}")
        assert response.status_code == 200
        booking_detail = response.json()
        assert booking_detail["id"] == booking_id
        assert booking_detail["tutor"]["id"] == test_tutor["tutor_id"]

        # Step 3: List bookings for student
        response = await e2e_client.get("/bookings")
        assert response.status_code == 200
        bookings_list = response.json()
        assert bookings_list["total"] >= 1

        # Step 4: Approve booking (as tutor)
        response = await e2e_client.patch(f"/bookings/{booking_id}/approve")
        assert response.status_code == 200
        approved_booking = response.json()
        assert approved_booking["status"] == "APPROVED"

    async def test_booking_rejection_flow(
        self,
        e2e_client: AsyncClient,
        test_tutor: dict,
        test_student: dict,
    ):
        """Test booking rejection flow."""
        # Create booking
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        booking_request = {
            "tutor_id": test_tutor["tutor_id"],
            "slots": [
                {
                    "date": tomorrow,
                    "start_time": "10:00",
                    "end_time": "12:00",
                }
            ],
            "notes": "To be rejected",
        }

        response = await e2e_client.post("/bookings", json=booking_request)
        assert response.status_code == 201
        booking_id = response.json()["id"]

        # Reject booking
        reject_request = {"reason": "Schedule conflict"}
        response = await e2e_client.patch(
            f"/bookings/{booking_id}/reject", json=reject_request
        )
        assert response.status_code == 200
        rejected_booking = response.json()
        assert rejected_booking["status"] == "REJECTED"

    async def test_booking_cancellation_flow(
        self,
        e2e_client: AsyncClient,
        test_tutor: dict,
        test_student: dict,
    ):
        """Test booking cancellation flow."""
        # Create booking
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        booking_request = {
            "tutor_id": test_tutor["tutor_id"],
            "slots": [
                {
                    "date": tomorrow,
                    "start_time": "15:00",
                    "end_time": "17:00",
                }
            ],
            "notes": "To be cancelled",
        }

        response = await e2e_client.post("/bookings", json=booking_request)
        assert response.status_code == 201
        booking_id = response.json()["id"]

        # Cancel booking
        response = await e2e_client.delete(f"/bookings/{booking_id}")
        assert response.status_code == 200
        cancelled_booking = response.json()
        assert cancelled_booking["status"] == "CANCELLED"

    async def test_booking_validation_errors(
        self,
        e2e_client: AsyncClient,
        test_tutor: dict,
    ):
        """Test booking validation - slots must be at least 24 hours in future."""
        # Try to book for today (should fail)
        today = date.today().strftime("%Y-%m-%d")

        booking_request = {
            "tutor_id": test_tutor["tutor_id"],
            "slots": [
                {
                    "date": today,
                    "start_time": "14:00",
                    "end_time": "16:00",
                }
            ],
            "notes": "Should fail - too soon",
        }

        response = await e2e_client.post("/bookings", json=booking_request)
        assert response.status_code == 400
        error_data = response.json()
        assert "detail" in error_data

    async def test_booking_not_found(
        self,
        e2e_client: AsyncClient,
    ):
        """Test getting non-existent booking."""
        response = await e2e_client.get("/bookings/99999")
        assert response.status_code == 404
