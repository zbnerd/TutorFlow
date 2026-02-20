# Load Tests for TutorFlow API

Load tests using Locust to verify the API can handle target traffic.

## Prerequisites

Install Locust:
```bash
pip install locust
```

## Running Load Tests

### Interactive Web UI:
```bash
cd backend
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 in your browser.

### Headless Mode (Command Line):
```bash
# Simulate 100 users, spawning 10 per second, running for 1 minute
locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 1m
```

### With Different Load Levels:
```bash
# Light load (50 users)
locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 50 -r 5 -t 2m

# Medium load (100 users)
locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 5m

# Heavy load (200 users)
locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 200 -r 20 -t 5m
```

## Test Scenarios

### TutorFlowUser (Read Operations)
- List bookings (3 weight)
- Get booking by ID (2 weight)
- Get tutor reviews (1 weight)
- Health check (1 weight)
- Get attendance status (1 weight)

### WriteUser (Write Operations)
- Create booking (1 weight)

## Performance Targets

- **Throughput**: 100 requests/second
- **Latency**: p95 < 200ms
- **Error Rate**: < 1%

## SLA Verification

The load test automatically checks SLA compliance:

```
=== SLA CHECK ===
PASSED: p95 latency (150ms) under 200ms threshold
PASSED: RPS (120.5) meets 100 req/s target

All SLAs passed!
```

## Test Data

The load test uses placeholder test data:
- `TEST_TUTOR_ID = 1`
- `TEST_STUDENT_ID = 2`

Update these values in `locustfile.py` to match your test database.

## Output

Locust generates:
- Real-time statistics in the web UI
- CSV files with request/response times
- Console output with SLA verification

## Tips

1. **Start with API server running**: Make sure the FastAPI server is running before starting load tests

2. **Use test database**: Never run load tests against production database

3. **Monitor resources**: Watch CPU, memory, and database connections during tests

4. **Gradual increase**: Start with low load and gradually increase to find breaking point

5. **Isolate tests**: Run load tests in an isolated environment

## Troubleshooting

### "Connection refused"
- Make sure the API server is running on the specified host/port

### High failure rate
- Check if test data exists in the database
- Verify endpoints are accessible
- Check server logs for errors

### Slow response times
- Check database connection pool
- Verify server has enough resources
- Check for blocking operations
