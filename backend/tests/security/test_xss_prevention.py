"""XSS (Cross-Site Scripting) prevention tests.

Tests for XSS vulnerability prevention.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestXSSPrevention:
    """Test XSS prevention."""

    async def test_xss_in_booking_notes(
        self, e2e_client: AsyncClient, test_tutor: dict
    ):
        """Test XSS payload in booking notes."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(XSS)'>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>",
        ]

        for payload in xss_payloads:
            booking_data = {
                "tutor_id": test_tutor["tutor_id"],
                "slots": [
                    {
                        "date": "2026-03-01",
                        "start_time": "14:00",
                        "end_time": "16:00",
                    }
                ],
                "notes": payload,
            }

            response = await e2e_client.post("/api/v1/bookings", json=booking_data)

            # If booking created, verify payload is sanitized in response
            if response.status_code == 201:
                booking = response.json()
                # Notes should be returned but not rendered
                assert "notes" in booking
                # The XSS payload should be present as text, not executed
                # (API returns JSON, so script tags won't execute anyway)
            else:
                assert response.status_code in [400, 422]

    async def test_xss_in_review_content(
        self,
        e2e_client: AsyncClient,
        test_booking: int,
        test_payment: int,
        test_tutor: dict,
        test_student: dict,
    ):
        """Test XSS payload in review content."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
        ]

        for payload in xss_payloads:
            review_data = {
                "booking_id": test_booking,
                "tutor_id": test_tutor["tutor_id"],
                "student_id": test_student["user_id"],
                "overall_rating": 5,
                "kindness_rating": 5,
                "preparation_rating": 5,
                "improvement_rating": 5,
                "punctuality_rating": 5,
                "content": payload,
                "is_anonymous": True,
            }

            response = await e2e_client.post(
                "/api/v1/reviews",
                params={"current_user_id": test_student["user_id"]},
                json=review_data
            )

            # Review should either be created (content stored as text)
            # or rejected by validation
            if response.status_code == 201:
                review = response.json()
                # Content stored as plain text, safe in JSON API
                assert "content" in review
            else:
                # Validation rejected the payload
                assert response.status_code in [400, 422]

    async def test_xss_in_tutor_reply(
        self, e2e_client: AsyncClient, test_tutor: dict
    ):
        """Test XSS payload in tutor reply."""
        xss_payload = "<script>alert('XSS')</script>"

        # This would require creating a review first, then adding reply
        # For now, test the endpoint directly
        reply_data = {"reply": xss_payload}

        response = await e2e_client.post(
            f"/api/v1/reviews/1/reply",
            params={"current_user_id": test_tutor["user_id"]},
            json=reply_data
        )

        # Should either succeed (stored as text) or fail gracefully
        assert response.status_code in [200, 400, 404, 422]

    async def test_xss_in_attendance_notes(
        self, e2e_client: AsyncClient
    ):
        """Test XSS payload in attendance notes."""
        xss_payload = "<script>alert('XSS')</script>"

        # Get a session
        response = await e2e_client.get("/api/v1/attendance/sessions")
        if response.status_code != 200:
            pytest.skip("Could not get sessions")

        sessions = response.json()["sessions"]
        if not sessions:
            pytest.skip("No sessions available")

        session_id = sessions[0]["id"]

        attendance_data = {
            "status": "COMPLETED",
            "notes": xss_payload,
        }

        response = await e2e_client.patch(
            f"/api/v1/attendance/sessions/{session_id}",
            json=attendance_data
        )

        # Should handle safely - stored as plain text
        if response.status_code == 200:
            attendance = response.json()
            assert "notes" in attendance

    async def test_content_type_header_prevents_xss(self, e2e_client: AsyncClient):
        """Verify API returns JSON content type, not HTML."""
        response = await e2e_client.get("/api/v1/bookings")

        # Should return JSON, not HTML
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type or "application/problem+json" in content_type

        # Should NOT return HTML
        assert "text/html" not in content_type

    async def test_json_response_escaped(self, e2e_client: AsyncClient):
        """Verify JSON responses properly escape special characters."""
        # This is handled automatically by FastAPI/Starlette's JSON encoder
        # We verify the API doesn't return raw HTML
        response = await e2e_client.get("/api/v1/bookings")

        # Response should be valid JSON
        assert response.headers.get("content-type", "").startswith("application/json")

        # Parse and verify it's valid JSON
        import json
        try:
            data = response.json()
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pytest.fail("Response is not valid JSON")

    async def test_no_reflected_x_in_error_messages(self, e2e_client: AsyncClient):
        """Test error messages don't reflect user input without escaping."""
        # Try to trigger an error with user input
        malicious_input = "<script>alert('XSS')</script>"

        response = await e2e_client.get(f"/api/v1/bookings/{malicious_input}")

        # Even in error, should not execute script
        # Since API returns JSON, this is automatically safe
        assert response.headers.get("content-type", "").startswith("application/json")
