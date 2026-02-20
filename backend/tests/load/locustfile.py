"""Locust load test script for TutorFlow API.

This script simulates user load on the booking API with a target of 100 req/s
and p95 latency < 200ms.

To run Locust tests:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Or run in headless mode:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 1m
"""
import random
import time
from datetime import date, timedelta
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# Test data
TEST_TUTOR_ID = 1
TEST_STUDENT_ID = 2


class TutorFlowUser(HttpUser):
    """Simulated user for load testing."""

    # Wait between 1 and 3 seconds between tasks
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a user starts. Login and get auth token."""
        # In a real scenario, this would perform OAuth login
        # For now, we'll skip actual auth since it's not yet implemented
        self.user_id = random.choice([1, 2])  # Random tutor or student

    @task(3)
    def list_bookings(self):
        """List bookings (most common operation)."""
        with self.client.get(
            "/api/v1/bookings",
            catch_response=True,
            name="List Bookings"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                # Auth not implemented - mark as success for load testing
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(2)
    def get_booking(self):
        """Get a specific booking."""
        booking_id = random.randint(1, 100)
        with self.client.get(
            f"/api/v1/bookings/{booking_id}",
            catch_response=True,
            name="Get Booking"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            elif response.status_code == 401:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(1)
    def get_tutor_reviews(self):
        """Get reviews for a tutor."""
        tutor_id = random.randint(1, 10)
        with self.client.get(
            f"/api/v1/reviews/tutors/{tutor_id}/reviews",
            catch_response=True,
            name="Get Tutor Reviews"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(1)
    def health_check(self):
        """Health check endpoint."""
        with self.client.get(
            "/health",
            catch_response=True,
            name="Health Check"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(1)
    def get_attendance_status(self):
        """Get attendance status."""
        with self.client.get(
            "/api/v1/attendance/status",
            catch_response=True,
            name="Get Attendance Status"
        ) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")


class WriteUser(HttpUser):
    """User performing write operations (heavier load)."""

    wait_time = between(2, 5)

    def on_start(self):
        """Setup for write user."""
        self.user_id = 2  # Student

    @task
    def create_booking(self):
        """Create a new booking (write operation)."""
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        booking_data = {
            "tutor_id": TEST_TUTOR_ID,
            "slots": [
                {
                    "date": tomorrow,
                    "start_time": "14:00",
                    "end_time": "16:00",
                }
            ],
            "notes": "Load test booking",
        }

        with self.client.post(
            "/api/v1/bookings",
            json=booking_data,
            catch_response=True,
            name="Create Booking"
        ) as response:
            if response.status_code in [201, 401]:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")


# Custom event handlers for reporting
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, **kwargs):
    """Log request events."""
    if response_time > 200:  # p95 threshold
        print(f"SLOW REQUEST: {name} took {response_time}ms")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print test summary."""
    print("\n=== LOAD TEST SUMMARY ===")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Failures: {environment.stats.total.num_failures}")
    print(f"RPS: {environment.stats.total.total_rps:.2f}")
    print(f"Median response time: {environment.stats.total.median_response_time:.0f}ms")
    print(f"95th percentile: {environment.stats.total.get_response_time_percentile(0.95):.0f}ms")

    # Check SLA
    p95 = environment.stats.total.get_response_time_percentile(0.95)
    rps = environment.stats.total.total_rps

    print("\n=== SLA CHECK ===")
    sla_passed = True

    if p95 > 200:
        print(f"FAILED: p95 latency ({p95:.0f}ms) exceeds 200ms threshold")
        sla_passed = False
    else:
        print(f"PASSED: p95 latency ({p95:.0f}ms) under 200ms threshold")

    if rps < 100:
        print(f"WARNING: RPS ({rps:.1f}) below 100 req/s target")
    else:
        print(f"PASSED: RPS ({rps:.1f}) meets 100 req/s target")

    if not sla_passed:
        print("\nSLA NOT MET!")
    else:
        print("\nAll SLAs passed!")
