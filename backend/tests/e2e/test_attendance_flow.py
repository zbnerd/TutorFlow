"""E2E test for the attendance flow.

Tests the flow: mark attendance → verify booking update
"""
import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from domain.entities import SessionStatus


@pytest.mark.asyncio
class TestAttendanceFlow:
    """Test attendance marking and booking update flow."""

    async def test_mark_attendance_flow(
        self,
        e2e_client: AsyncClient,
        test_booking: int,
    ):
        """Test marking attendance for a session."""
        # First, get sessions for the booking
        response = await e2e_client.get("/attendance/sessions")
        assert response.status_code == 200
        sessions_data = response.json()
        assert sessions_data["total"] >= 1

        # Get the first session ID
        session_id = sessions_data["sessions"][0]["id"]
        assert sessions_data["sessions"][0]["status"] == "SCHEDULED"

        # Mark attendance as ATTENDED
        attendance_request = {
            "status": "COMPLETED",
            "notes": "Student attended and participated well",
        }

        response = await e2e_client.patch(
            f"/attendance/sessions/{session_id}", json=attendance_request
        )
        assert response.status_code == 200
        attendance_response = response.json()
        assert attendance_response["status"] == "COMPLETED"
        assert attendance_response["attendance_checked_at"] is not None
        assert attendance_response["notes"] == "Student attended and participated well"

        # Verify the session status is updated
        response = await e2e_client.get(f"/attendance/sessions?status=SCHEDULED")
        assert response.status_code == 200
        remaining_sessions = response.json()
        # The marked session should no longer be in SCHEDULED status
        assert remaining_sessions["total"] < sessions_data["total"]

    async def test_mark_no_show_flow(
        self,
        e2e_client: AsyncClient,
        test_booking: int,
    ):
        """Test marking a session as NO_SHOW."""
        # Get sessions
        response = await e2e_client.get("/attendance/sessions")
        assert response.status_code == 200
        sessions_data = response.json()

        if sessions_data["total"] == 0:
            pytest.skip("No sessions available for testing")

        # Get a scheduled session
        scheduled_sessions = [
            s for s in sessions_data["sessions"] if s["status"] == "SCHEDULED"
        ]
        if not scheduled_sessions:
            pytest.skip("No scheduled sessions available")

        session_id = scheduled_sessions[0]["id"]

        # Mark as NO_SHOW
        attendance_request = {
            "status": "NO_SHOW",
            "notes": "Student did not show up without notice",
        }

        response = await e2e_client.patch(
            f"/attendance/sessions/{session_id}", json=attendance_request
        )
        assert response.status_code == 200
        attendance_response = response.json()
        assert attendance_response["status"] == "NO_SHOW"

    async def test_attendance_status_summary(
        self,
        e2e_client: AsyncClient,
        test_booking: int,
    ):
        """Test getting attendance status summary."""
        response = await e2e_client.get("/attendance/status")
        assert response.status_code == 200
        status_data = response.json()
        assert "total" in status_data
        assert "by_status" in status_data
        assert "recent_sessions" in status_data
        assert isinstance(status_data["total"], int)
        assert isinstance(status_data["by_status"], dict)

    async def test_mark_already_marked_session_fails(
        self,
        e2e_client: AsyncClient,
        test_booking: int,
    ):
        """Test that marking an already marked session fails."""
        # Get sessions
        response = await e2e_client.get("/attendance/sessions")
        assert response.status_code == 200
        sessions_data = response.json()

        if sessions_data["total"] == 0:
            pytest.skip("No sessions available for testing")

        # Find a session that's already marked
        marked_sessions = [
            s for s in sessions_data["sessions"]
            if s["status"] in [SessionStatus.COMPLETED.value, SessionStatus.NO_SHOW.value]
        ]

        if not marked_sessions:
            # Mark a session first
            scheduled_sessions = [
                s for s in sessions_data["sessions"] if s["status"] == "SCHEDULED"
            ]
            if not scheduled_sessions:
                pytest.skip("No sessions to test with")

            session_id = scheduled_sessions[0]["id"]
            attendance_request = {"status": "COMPLETED", "notes": "First mark"}
            await e2e_client.patch(
                f"/attendance/sessions/{session_id}", json=attendance_request
            )
        else:
            session_id = marked_sessions[0]["id"]

        # Try to mark again - should fail
        attendance_request = {"status": "COMPLETED", "notes": "Duplicate mark"}
        response = await e2e_client.patch(
            f"/attendance/sessions/{session_id}", json=attendance_request
        )
        assert response.status_code == 400

    async def test_invalid_attendance_status(
        self,
        e2e_client: AsyncClient,
        test_booking: int,
    ):
        """Test that invalid attendance status is rejected."""
        # Get a session
        response = await e2e_client.get("/attendance/sessions")
        assert response.status_code == 200
        sessions_data = response.json()

        if sessions_data["total"] == 0:
            pytest.skip("No sessions available for testing")

        session_id = sessions_data["sessions"][0]["id"]

        # Try invalid status
        attendance_request = {"status": "INVALID_STATUS", "notes": "Test"}
        response = await e2e_client.patch(
            f"/attendance/sessions/{session_id}", json=attendance_request
        )
        assert response.status_code == 422  # Validation error

    async def test_attendance_date_filtering(
        self,
        e2e_client: AsyncClient,
        test_booking: int,
    ):
        """Test filtering sessions by date range."""
        today = date.today()
        next_week = today + timedelta(weeks=1)

        # Get sessions for next week
        response = await e2e_client.get(
            "/attendance/sessions",
            params={
                "date_from": next_week.strftime("%Y-%m-%d"),
                "date_to": (next_week + timedelta(days=7)).strftime("%Y-%m-%d"),
            }
        )
        assert response.status_code == 200
        filtered_sessions = response.json()
        assert "sessions" in filtered_sessions
        assert "total" in filtered_sessions
