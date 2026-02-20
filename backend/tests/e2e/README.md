# E2E Tests for TutorFlow API

End-to-end tests for the TutorFlow backend API using httpx (async HTTP client).

## Directory Structure

```
tests/e2e/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── pytest.ini               # Pytest configuration
├── playwright.config.ts     # Playwright config (template, not yet installed)
├── fixtures/                # Additional test fixtures
│   └── __init__.py
├── helpers/                 # Helper utilities
│   ├── __init__.py
│   ├── api_client.py        # API client helper class
│   └── test_data.py         # Test data factory
├── test_booking_flow.py     # Booking flow E2E tests
├── test_attendance_flow.py  # Attendance flow E2E tests
└── test_review_flow.py      # Review flow E2E tests
```

## Running E2E Tests

### Run all E2E tests:
```bash
cd backend
pytest tests/e2e/ -v
```

### Run specific test file:
```bash
pytest tests/e2e/test_booking_flow.py -v
```

### Run with coverage:
```bash
pytest tests/e2e/ --cov=../ --cov-report=html
```

### Run specific marker:
```bash
pytest tests/e2e/ -m booking -v
pytest tests/e2e/ -m "e2e and slow" -v
```

## Test Fixtures

The following fixtures are available in `conftest.py`:

### Core Fixtures:
- `e2e_engine` - Test database engine (in-memory SQLite)
- `e2e_session` - Database session for tests
- `e2e_client` - HTTP client for API requests

### Data Fixtures:
- `test_tutor` - Creates an approved tutor user
- `test_student` - Creates a student user
- `test_available_slot` - Creates an available slot for tutor
- `test_booking` - Creates a booking with sessions
- `test_payment` - Creates a paid payment record
- `auth_headers` - Generates JWT auth headers

## Test Flows

### 1. Booking Flow (`test_booking_flow.py`)
Tests the complete booking lifecycle:
- Create booking request
- Approve/reject booking
- Cancel booking
- Validation errors (24-hour minimum, etc.)

### 2. Attendance Flow (`test_attendance_flow.py`)
Tests attendance marking:
- Mark session as attended
- Mark session as no-show
- Get attendance status summary
- Prevent double-marking
- Date filtering

### 3. Review Flow (`test_review_flow.py`)
Tests the review system:
- Create review (verified payment only)
- Update review (within 7 days)
- Delete review (within 7 days)
- Tutor reply to review
- Report review for moderation
- Filter by rating

## Helper Classes

### APIClient (`helpers/api_client.py`)
Convenience methods for API calls:
```python
from tests.e2e.helpers.api_client import APIClient

async def test_example(e2e_client):
    api = APIClient(e2e_client)
    booking = await api.create_booking(
        tutor_id=1,
        slots=[{"date": "2026-02-25", "start_time": "14:00", "end_time": "16:00"}]
    )
```

### TestDataFactory (`helpers/test_data.py`)
Factory for creating test data:
```python
from tests.e2e.helpers.test_data import TestDataFactory

async def test_example(e2e_session):
    factory = TestDataFactory(e2e_session)
    user, tutor = await factory.create_tutor()
    booking = await factory.create_booking(
        tutor_id=tutor.id,
        student_id=2
    )
```

## Future: Playwright Integration

When Playwright is installed, browser-based E2E tests can be added:

```bash
# Install Playwright
npm install -D @playwright/test
npx playwright install
```

The `playwright.config.ts` file is pre-configured for when Playwright is needed.

## Test Data Cleanup

All fixtures use auto-cleanup:
- Database is dropped after each test function
- In-memory SQLite ensures isolation
- No manual cleanup needed

## Notes

- Tests use placeholder `user_id` values where JWT auth is not yet implemented
- Some tests may skip if required data is not available
- All dates are relative to `date.today()` to avoid test brittleness
