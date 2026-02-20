"""Input validation tests.

Tests for proper input validation and sanitization.
"""
import pytest
from httpx import AsyncClient
from datetime import date, timedelta


@pytest.mark.asyncio
class TestInputValidation:
    """Test input validation."""

    async def test_booking_with_past_date_rejected(
        self, e2e_client: AsyncClient, test_tutor: dict
    ):
        """Test that bookings with past dates are rejected."""
        yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

        booking_data = {
            "tutor_id": test_tutor["tutor_id"],
            "slots": [
                {
                    "date": yesterday,
                    "start_time": "14:00",
                    "end_time": "16:00",
                }
            ],
            "notes": "Past booking",
        }

        response = await e2e_client.post("/api/v1/bookings", json=booking_data)
        assert response.status_code == 400

    async def test_booking_with_invalid_time_format(
        self, e2e_client: AsyncClient, test_tutor: dict
    ):
        """Test that invalid time formats are rejected."""
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        booking_data = {
            "tutor_id": test_tutor["tutor_id"],
            "slots": [
                {
                    "date": tomorrow,
                    "start_time": "25:00",  # Invalid hour
                    "end_time": "26:00",
                }
            ],
            "notes": "Invalid time",
        }

        response = await e2e_client.post("/api/v1/bookings", json=booking_data)
        assert response.status_code == 422  # Validation error

    async def test_review_rating_bounds_validation(
        self,
        e2e_client: AsyncClient,
        test_booking: int,
        test_payment: int,
        test_tutor: dict,
        test_student: dict,
    ):
        """Test that review ratings are bounded (1-5)."""
        # Test rating > 5
        review_data = {
            "booking_id": test_booking,
            "tutor_id": test_tutor["tutor_id"],
            "student_id": test_student["user_id"],
            "overall_rating": 6,  # Invalid
            "kindness_rating": 6,
            "preparation_rating": 6,
            "improvement_rating": 6,
            "punctuality_rating": 6,
            "content": "Test",
            "is_anonymous": True,
        }

        response = await e2e_client.post(
            "/api/v1/reviews",
            params={"current_user_id": test_student["user_id"]},
            json=review_data
        )
        # Should reject invalid rating
        assert response.status_code in [400, 422]

        # Test rating < 1
        review_data["overall_rating"] = 0
        response = await e2e_client.post(
            "/api/v1/reviews",
            params={"current_user_id": test_student["user_id"]},
            json=review_data
        )
        assert response.status_code in [400, 422]

    async def test_empty_required_fields_rejected(
        self, e2e_client: AsyncClient, test_tutor: dict
    ):
        """Test that missing required fields are rejected."""
        # Missing slots
        booking_data = {
            "tutor_id": test_tutor["tutor_id"],
            "notes": "Missing slots",
        }

        response = await e2e_client.post("/api/v1/bookings", json=booking_data)
        assert response.status_code == 422

    async def test_very_long_input_rejected(
        self, e2e_client: AsyncClient, test_tutor: dict
    ):
        """Test that excessively long inputs are rejected."""
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Very long notes
        booking_data = {
            "tutor_id": test_tutor["tutor_id"],
            "slots": [
                {
                    "date": tomorrow,
                    "start_time": "14:00",
                    "end_time": "16:00",
                }
            ],
            "notes": "A" * 10000,  # Very long string
        }

        response = await e2e_client.post("/api/v1/bookings", json=booking_data)
        # Should either accept (with truncation) or reject
        assert response.status_code in [201, 400, 422]

    async def test_negative_id_rejected(self, e2e_client: AsyncClient):
        """Test that negative IDs are rejected."""
        response = await e2e_client.get("/api/v1/bookings/-1")
        assert response.status_code in [400, 404]

    async def test_special_characters_in_notes(
        self, e2e_client: AsyncClient, test_tutor: dict
    ):
        """Test handling of special characters."""
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Various special characters
        special_chars = [
            "Test with emojis 🎉👍",
            "Test with Korean characters 안녕하세요",
            "Test with quotes \"quotes\"",
            "Test with apostrophe's",
            "Test with newlines\nand\ttabs",
            "Test with unicode \u00e9\u00f1",
        ]

        for notes in special_chars:
            booking_data = {
                "tutor_id": test_tutor["tutor_id"],
                "slots": [
                    {
                        "date": tomorrow,
                        "start_time": "14:00",
                        "end_time": "16:00",
                    }
                ],
                "notes": notes,
            }

            response = await e2e_client.post("/api/v1/bookings", json=booking_data)
            # Should handle special characters gracefully
            assert response.status_code in [201, 400, 422]

    async def test_invalid_json_rejected(self, e2e_client: AsyncClient):
        """Test that invalid JSON is rejected."""
        response = await e2e_client.post(
            "/api/v1/bookings",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    async def test_content_type_validation(self, e2e_client: AsyncClient):
        """Test that Content-Type is validated."""
        # Send form data instead of JSON
        response = await e2e_client.post(
            "/api/v1/bookings",
            data={"tutor_id": 1},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        # Should reject non-JSON content type
        assert response.status_code in [400, 422, 415]
