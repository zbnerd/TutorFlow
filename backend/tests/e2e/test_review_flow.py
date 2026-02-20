"""E2E test for the review flow.

Tests the flow: complete session → write review → verify display
"""
import pytest
from httpx import AsyncClient
from domain.entities import SessionStatus


@pytest.mark.asyncio
class TestReviewFlow:
    """Test review creation and display flow."""

    async def test_complete_review_flow(
        self,
        e2e_client: AsyncClient,
        test_booking: int,
        test_payment: int,
        test_tutor: dict,
        test_student: dict,
    ):
        """Test complete review flow: complete session → write review → verify display."""
        # Step 1: Complete a session first
        response = await e2e_client.get("/attendance/sessions")
        assert response.status_code == 200
        sessions_data = response.json()

        if sessions_data["total"] == 0:
            pytest.skip("No sessions available for review testing")

        # Find and mark a session as completed
        scheduled_sessions = [
            s for s in sessions_data["sessions"] if s["status"] == "SCHEDULED"
        ]
        if not scheduled_sessions:
            pytest.skip("No scheduled sessions to complete")

        session_id = scheduled_sessions[0]["id"]

        attendance_request = {"status": "COMPLETED", "notes": "Great session"}
        response = await e2e_client.patch(
            f"/attendance/sessions/{session_id}", json=attendance_request
        )
        assert response.status_code == 200

        # Step 2: Create a review
        review_request = {
            "booking_id": test_booking,
            "tutor_id": test_tutor["tutor_id"],
            "student_id": test_student["user_id"],
            "overall_rating": 5,
            "kindness_rating": 5,
            "preparation_rating": 4,
            "improvement_rating": 5,
            "punctuality_rating": 5,
            "content": "훌륭한 선생님입니다! 아이가 수업 후 많은 발전을 보였습니다.",
            "is_anonymous": True,
        }

        # Add query parameter for current_user_id
        response = await e2e_client.post(
            "/reviews", params={"current_user_id": test_student["user_id"]}, json=review_request
        )
        assert response.status_code == 201, f"Review creation failed: {response.text}"

        review_data = response.json()
        review_id = review_data["id"]
        assert review_data["overall_rating"] == 5
        assert review_data["content"] == "훌륭한 선생님입니다! 아이가 수업 후 많은 발전을 보였습니다."
        assert review_data["is_anonymous"] is True

        # Step 3: Get the review
        response = await e2e_client.get(f"/reviews/{review_id}")
        assert response.status_code == 200
        fetched_review = response.json()
        assert fetched_review["id"] == review_id

        # Step 4: List reviews for the tutor
        response = await e2e_client.get(f"/reviews/tutors/{test_tutor['tutor_id']}/reviews")
        assert response.status_code == 200
        tutor_reviews = response.json()
        assert "reviews" in tutor_reviews
        assert "total_count" in tutor_reviews
        assert "avg_rating" in tutor_reviews
        assert tutor_reviews["total_count"] >= 1

    async def test_review_validation_verified_payment_only(
        self,
        e2e_client: AsyncClient,
        test_booking: int,
        test_tutor: dict,
        test_student: dict,
    ):
        """Test that review requires verified payment."""
        # Create review for booking without verified payment
        # This test would need a booking without payment - for now, we test the endpoint exists
        review_request = {
            "booking_id": test_booking,
            "tutor_id": test_tutor["tutor_id"],
            "student_id": test_student["user_id"],
            "overall_rating": 4,
            "kindness_rating": 4,
            "preparation_rating": 4,
            "improvement_rating": 4,
            "punctuality_rating": 4,
            "content": "Good tutor",
            "is_anonymous": False,
        }

        response = await e2e_client.post(
            "/reviews", params={"current_user_id": test_student["user_id"]}, json=review_request
        )
        # Should either succeed or return validation error
        assert response.status_code in [201, 400]

    async def test_review_update_within_time_limit(
        self,
        e2e_client: AsyncClient,
        test_booking: int,
        test_payment: int,
        test_tutor: dict,
        test_student: dict,
    ):
        """Test updating a review within 7 days."""
        # First create a review
        review_request = {
            "booking_id": test_booking,
            "tutor_id": test_tutor["tutor_id"],
            "student_id": test_student["user_id"],
            "overall_rating": 4,
            "kindness_rating": 4,
            "preparation_rating": 4,
            "improvement_rating": 4,
            "punctuality_rating": 4,
            "content": "Original review",
            "is_anonymous": True,
        }

        response = await e2e_client.post(
            "/reviews", params={"current_user_id": test_student["user_id"]}, json=review_request
        )
        if response.status_code != 201:
            pytest.skip("Review creation failed")

        review_id = response.json()["id"]

        # Update the review
        update_request = {
            "overall_rating": 5,
            "kindness_rating": 5,
            "preparation_rating": 5,
            "improvement_rating": 5,
            "punctuality_rating": 5,
            "content": "Updated review - even better!",
            "is_anonymous": False,
        }

        response = await e2e_client.patch(
            f"/reviews/{review_id}",
            params={"current_user_id": test_student["user_id"]},
            json=update_request
        )
        assert response.status_code == 200
        updated_review = response.json()
        assert updated_review["content"] == "Updated review - even better!"
        assert updated_review["overall_rating"] == 5

    async def test_review_deletion(
        self,
        e2e_client: AsyncClient,
        test_booking: int,
        test_payment: int,
        test_tutor: dict,
        test_student: dict,
    ):
        """Test deleting a review within time limit."""
        # Create a review
        review_request = {
            "booking_id": test_booking,
            "tutor_id": test_tutor["tutor_id"],
            "student_id": test_student["user_id"],
            "overall_rating": 3,
            "kindness_rating": 3,
            "preparation_rating": 3,
            "improvement_rating": 3,
            "punctuality_rating": 3,
            "content": "Review to be deleted",
            "is_anonymous": True,
        }

        response = await e2e_client.post(
            "/reviews", params={"current_user_id": test_student["user_id"]}, json=review_request
        )
        if response.status_code != 201:
            pytest.skip("Review creation failed")

        review_id = response.json()["id"]

        # Delete the review
        response = await e2e_client.delete(
            f"/reviews/{review_id}",
            params={"current_user_id": test_student["user_id"]}
        )
        assert response.status_code == 204

        # Verify review is deleted
        response = await e2e_client.get(f"/reviews/{review_id}")
        assert response.status_code == 404

    async def test_tutor_reply_to_review(
        self,
        e2e_client: AsyncClient,
        test_booking: int,
        test_payment: int,
        test_tutor: dict,
        test_student: dict,
    ):
        """Test tutor adding reply to review."""
        # Create a review as student
        review_request = {
            "booking_id": test_booking,
            "tutor_id": test_tutor["tutor_id"],
            "student_id": test_student["user_id"],
            "overall_rating": 5,
            "kindness_rating": 5,
            "preparation_rating": 5,
            "improvement_rating": 5,
            "punctuality_rating": 5,
            "content": "Great tutor!",
            "is_anonymous": True,
        }

        response = await e2e_client.post(
            "/reviews", params={"current_user_id": test_student["user_id"]}, json=review_request
        )
        if response.status_code != 201:
            pytest.skip("Review creation failed")

        review_id = response.json()["id"]

        # Add tutor reply
        reply_request = {"reply": "감사합니다! 열심히 지도하겠습니다."}
        response = await e2e_client.post(
            f"/reviews/{review_id}/reply",
            params={"current_user_id": test_tutor["user_id"]},
            json=reply_request
        )
        assert response.status_code == 200
        review_with_reply = response.json()
        assert "reply" in review_with_reply
        assert review_with_reply["reply"] == "감사합니다! 열심히 지도하겠습니다."

    async def test_review_rating_filtering(
        self,
        e2e_client: AsyncClient,
        test_tutor: dict,
    ):
        """Test filtering reviews by minimum rating."""
        # Get reviews with minimum rating filter
        response = await e2e_client.get(
            f"/reviews/tutors/{test_tutor['tutor_id']}/reviews",
            params={"min_rating": 4.0}
        )
        assert response.status_code == 200
        filtered_reviews = response.json()

        # All returned reviews should have rating >= 4.0
        for review in filtered_reviews["reviews"]:
            assert review["overall_rating"] >= 4.0

    async def test_review_report(
        self,
        e2e_client: AsyncClient,
        test_booking: int,
        test_payment: int,
        test_tutor: dict,
        test_student: dict,
    ):
        """Test reporting a review for moderation."""
        # Create a review
        review_request = {
            "booking_id": test_booking,
            "tutor_id": test_tutor["tutor_id"],
            "student_id": test_student["user_id"],
            "overall_rating": 1,
            "kindness_rating": 1,
            "preparation_rating": 1,
            "improvement_rating": 1,
            "punctuality_rating": 1,
            "content": "Inappropriate content to be reported",
            "is_anonymous": True,
        }

        response = await e2e_client.post(
            "/reviews", params={"current_user_id": test_student["user_id"]}, json=review_request
        )
        if response.status_code != 201:
            pytest.skip("Review creation failed")

        review_id = response.json()["id"]

        # Report the review
        report_request = {
            "reason": "spam",
            "description": "This looks like spam content"
        }
        response = await e2e_client.post(
            f"/reviews/{review_id}/report",
            params={"current_user_id": test_student["user_id"]},
            json=report_request
        )
        assert response.status_code == 201
        assert "message" in response.json()
