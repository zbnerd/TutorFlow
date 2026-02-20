# Monitoring and Metrics Infrastructure

This directory contains all monitoring, logging, and metrics configurations for TutorFlow API.

## Directory Structure

```
monitoring/
├── __init__.py
├── README.md                      # This file
├── prometheus/
│   ├── __init__.py
│   ├── metrics.py                 # Prometheus metrics definitions
│   └── prometheus.yml             # Prometheus configuration template
├── grafana/
│   ├── __init__.py
│   ├── api-dashboard.json         # API performance dashboard
│   └── business-dashboard.json    # Business metrics dashboard
├── logs/
│   ├── __init__.py
│   └── config.py                  # Structured JSON logging configuration
├── health.py                      # Health check endpoints
└── middleware.py                  # Performance tracking middleware
```

## Setup Instructions

### 1. Install Dependencies

Add to `requirements.txt`:
```txt
# Monitoring
prometheus-client==0.21.0
python-json-logger==3.2.1
psutil==6.1.0
```

Install:
```bash
pip install prometheus-client python-json-logger psutil
```

### 2. Integrate with FastAPI Application

In `main.py`, add the following:

```python
from fastapi import FastAPI
from monitoring.prometheus.metrics import init_metrics, metrics_endpoint
from monitoring.health import router as health_router
from monitoring.middleware import PerformanceTrackingMiddleware
from monitoring.logs.config import setup_logging

# Initialize logging
setup_logging(level="INFO")

# Create app
app = FastAPI()

# Initialize metrics
init_metrics(app_name="tutorflow-api", app_version="1.0.0")

# Add middleware
app.add_middleware(PerformanceTrackingMiddleware)

# Include health check routes
app.include_router(health_router, prefix="/health")

# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    return await metrics_endpoint()
```

### 3. Configure Prometheus (Optional)

If deploying Prometheus as a metrics collector:

```bash
# Install Prometheus
# Download from https://prometheus.io/download/

# Copy configuration
cp monitoring/prometheus/prometheus.yml /etc/prometheus/prometheus.yml

# Start Prometheus
prometheus --config.file=/etc/prometheus/prometheus.yml
```

### 4. Configure Grafana Dashboards (Optional)

```bash
# Install Grafana
# Download from https://grafana.com/grafana/download

# Import dashboards:
# 1. Open Grafana web UI (default: http://localhost:3000)
# 2. Go to Dashboards -> Import
# 3. Upload monitoring/grafana/api-dashboard.json
# 4. Upload monitoring/grafana/business-dashboard.json
```

## Available Metrics

### HTTP Metrics
- `tutorflow_http_requests_total` - Total HTTP requests (by method, endpoint, status)
- `tutorflow_http_request_duration_seconds` - Request latency histogram
- `tutorflow_http_requests_active` - Current active requests

### Database Metrics
- `tutorflow_db_connections_active` - Active database connections
- `tutorflow_db_connections_idle` - Idle database connections

### Business Metrics
- `tutorflow_bookings_total` - Total bookings created (by status)
- `tutorflow_payments_total` - Total payments processed (by status)
- `tutorflow_reviews_total` - Total reviews created
- `tutorflow_attendance_marked_total` - Total attendance marked (by status)

### Error Metrics
- `tutorflow_errors_total` - Total errors (by type, endpoint)

### External Service Metrics
- `tutorflow_external_service_calls_total` - External service calls (by service, operation, status)
- `tutorflow_external_service_duration_seconds` - External service latency

## Health Check Endpoints

### `/health` - Basic Health Check
Returns basic health status.
```json
{
  "status": "healthy",
  "timestamp": "2026-02-20T10:00:00",
  "version": "1.0.0"
}
```

### `/health/detailed` - Detailed Health Check
Returns all component statuses.
```json
{
  "status": "healthy",
  "timestamp": "2026-02-20T10:00:00",
  "version": "1.0.0",
  "components": {
    "database": { "status": "healthy" },
    "external_services": { ... }
  },
  "system": { ... }
}
```

### `/health/ready` - Readiness Probe
For Kubernetes/Docker deployments. Returns 200 if ready to serve traffic.

### `/health/live` - Liveness Probe
For Kubernetes/Docker deployments. Returns 200 if the application is running.

### `/health/db` - Database Health Check
Specific database connectivity check.

## Logging

### Structured JSON Logging

Logs are output as JSON for easy parsing:

```json
{
  "timestamp": "2026-02-20T10:00:00.123456",
  "level": "INFO",
  "logger": "tutorflow.request",
  "module": "monitoring",
  "function": "log_request",
  "line": 42,
  "app": "tutorflow-api",
  "environment": "production",
  "version": "1.0.0",
  "http_method": "GET",
  "http_path": "/api/v1/bookings",
  "http_status": 200,
  "duration_ms": 45.2,
  "user_id": 123,
  "request_id": "abc-123-def"
}
```

### Usage in Code

```python
from monitoring.logs.config import get_logger, log_business_event

logger = get_logger(__name__)
logger.info("Processing booking", extra={"booking_id": 123})

# Or use helper functions
log_business_event(
    event_type="booking_created",
    event_data={"booking_id": 123, "amount": 50000},
    user_id=456
)
```

## Performance Middleware

The `PerformanceTrackingMiddleware` automatically:
- Tracks HTTP request metrics
- Logs all requests with timing
- Adds `X-Request-ID` header
- Tracks errors

## Grafana Dashboards

### API Dashboard
- Request rate
- Request latency (p95, p99)
- Active requests
- Error rate
- Database connection pool

### Business Dashboard
- Booking creation rate
- Payment processing rate
- Review creation rate
- Attendance marking rate
- External service call rate
- External service latency

## Alerts (Template)

Create `monitoring/prometheus/alerts.yml`:

```yaml
groups:
  - name: tutorflow_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(tutorflow_errors_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(tutorflow_http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        annotations:
          summary: "p95 latency exceeds 1 second"

      - alert: DatabaseConnectionPoolExhausted
        expr: tutorflow_db_connections_active / (tutorflow_db_connections_active + tutorflow_db_connections_idle) > 0.9
        for: 5m
        annotations:
          summary: "Database connection pool nearly exhausted"
```

## Notes

- All monitoring components are optional and can be used independently
- Prometheus/Grafana setup is optional - metrics are exposed via `/metrics` endpoint
- Health checks work without external dependencies
- Logging works out of the box after setup
