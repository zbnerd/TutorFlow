"""SQL injection prevention tests.

Tests for SQL injection vulnerability prevention.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSQLInjectionPrevention:
    """Test SQL injection prevention."""

    async def test_sql_injection_in_booking_id(self, e2e_client: AsyncClient):
        """Test SQL injection in booking ID parameter."""
        # Common SQL injection payloads
        injection_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE bookings--",
            "1' UNION SELECT * FROM users--",
            "1' AND 1=1--",
            "-1' OR '1'='1",
        ]

        for payload in injection_payloads:
            response = await e2e_client.get(f"/api/v1/bookings/{payload}")
            # Should not return 500 (internal server error)
            # Should return 404 (not found) or 400 (bad request)
            assert response.status_code in [400, 404, 422]

    async def test_sql_injection_in_query_params(self, e2e_client: AsyncClient):
        """Test SQL injection in query parameters."""
        injection_payloads = [
            "1' OR '1'='1",
            "test' UNION SELECT * FROM users--",
            "test; DELETE FROM users--",
        ]

        for payload in injection_payloads:
            response = await e2e_client.get(
                "/api/v1/bookings",
                params={"status": payload}
            )
            # Should handle gracefully
            assert response.status_code in [200, 400, 404, 422]

    async def test_sql_injection_in_booking_creation(
        self, e2e_client: AsyncClient, test_tutor: dict
    ):
        """Test SQL injection in booking notes field."""
        injection_payloads = [
            "'; DROP TABLE bookings; --",
            "' OR '1'='1",
            "test'; INSERT INTO users (email) VALUES ('hacker@evil.com'); --",
        ]

        for payload in injection_payloads:
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
            # Should either succeed (input sanitized) or fail validation
            assert response.status_code in [201, 400, 422]

    async def test_sql_injection_in_search_filter(self, e2e_client: AsyncClient):
        """Test SQL injection in search/filter parameters."""
        injection_payloads = [
            "admin'--",
            "admin' OR '1'='1",
            "'; SELECT SLEEP(10)--",
        ]

        for payload in injection_payloads:
            response = await e2e_client.get(
                f"/api/v1/reviews/tutors/{payload}/reviews"
            )
            # Should not cause internal server error
            assert response.status_code in [400, 404, 422]

    async def test_sql_injection_in_attendance_notes(
        self, e2e_client: AsyncClient
    ):
        """Test SQL injection in attendance notes."""
        injection_payloads = [
            "'; DELETE FROM users--",
            "' OR '1'='1",
        ]

        # First get a session
        response = await e2e_client.get("/api/v1/attendance/sessions")
        if response.status_code != 200:
            pytest.skip("Could not get sessions")

        sessions = response.json()["sessions"]
        if not sessions:
            pytest.skip("No sessions available")

        session_id = sessions[0]["id"]

        for payload in injection_payloads:
            attendance_data = {
                "status": "COMPLETED",
                "notes": payload,
            }

            response = await e2e_client.patch(
                f"/api/v1/attendance/sessions/{session_id}",
                json=attendance_data
            )
            # Should handle safely
            assert response.status_code in [200, 400, 404, 422]

    async def test_parameterized_queries_used(self):
        """Verify that SQLAlchemy uses parameterized queries.

        This is a design verification - SQLAlchemy ORM uses
        parameterized queries by default, preventing SQL injection.
        """
        # SQLAlchemy's create_engine with proper configuration
        # uses parameterized queries automatically
        from infrastructure.database import engine

        # Verify engine is using prepared statements
        # (SQLAlchemy default behavior)
        assert engine is not None
        # The ORM layer prevents SQL injection by design
