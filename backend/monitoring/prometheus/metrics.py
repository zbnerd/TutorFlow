"""Prometheus metrics for TutorFlow API.

This module defines all Prometheus metrics for monitoring the application.
Uses prometheus_client for metrics exposition.
"""
import time
from functools import wraps
from typing import Callable, Any
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry
from fastapi import Request, Response
from fastapi.responses import Response as FastAPIResponse


# Create a custom registry for our metrics
registry = CollectorRegistry()

# Application info
app_info = Info(
    "tutorflow_application",
    "TutorFlow application information",
    registry=registry
)

# HTTP request counter
http_requests_total = Counter(
    "tutorflow_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry
)

# HTTP request duration histogram
http_request_duration_seconds = Histogram(
    "tutorflow_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0),
    registry=registry
)

# Active requests gauge
http_requests_active = Gauge(
    "tutorflow_http_requests_active",
    "Number of active HTTP requests",
    registry=registry
)

# Database connection pool gauge
db_connections_active = Gauge(
    "tutorflow_db_connections_active",
    "Active database connections",
    registry=registry
)

db_connections_idle = Gauge(
    "tutorflow_db_connections_idle",
    "Idle database connections",
    registry=registry
)

# Business metrics
bookings_total = Counter(
    "tutorflow_bookings_total",
    "Total bookings created",
    ["status"],
    registry=registry
)

payments_total = Counter(
    "tutorflow_payments_total",
    "Total payments processed",
    ["status"],
    registry=registry
)

reviews_total = Counter(
    "tutorflow_reviews_total",
    "Total reviews created",
    registry=registry
)

attendance_marked_total = Counter(
    "tutorflow_attendance_marked_total",
    "Total attendance marked",
    ["status"],
    registry=registry
)

# Error tracking
errors_total = Counter(
    "tutorflow_errors_total",
    "Total errors",
    ["error_type", "endpoint"],
    registry=registry
)

# External service calls
external_service_calls_total = Counter(
    "tutorflow_external_service_calls_total",
    "Total external service calls",
    ["service", "operation", "status"],
    registry=registry
)

external_service_duration_seconds = Histogram(
    "tutorflow_external_service_duration_seconds",
    "External service call duration in seconds",
    ["service", "operation"],
    buckets=(.1, .25, .5, 1.0, 2.5, 5.0, 10.0),
    registry=registry
)


def init_metrics(app_name: str, app_version: str):
    """Initialize application info metrics."""
    app_info.info({
        "name": app_name,
        "version": app_version,
    })


def track_request_time(func: Callable) -> Callable:
    """Decorator to track request duration for async functions."""
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        http_requests_active.inc()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            http_request_duration_seconds.observe(duration)
            http_requests_active.dec()
    return wrapper


def track_external_call(service: str, operation: str):
    """Decorator to track external service calls."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                errors_total.labels(
                    error_type=type(e).__name__,
                    endpoint=f"{service}_{operation}"
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                external_service_duration_seconds.labels(
                    service=service,
                    operation=operation
                ).observe(duration)
                external_service_calls_total.labels(
                    service=service,
                    operation=operation,
                    status=status
                ).inc()
        return wrapper
    return decorator


async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    """FastAPI middleware to track HTTP metrics."""
    start_time = time.time()
    method = request.method
    path = request.url.path

    # Skip metrics endpoint itself
    if path == "/metrics":
        return await call_next(request)

    http_requests_active.inc()

    try:
        response = await call_next(request)
        status = response.status_code

        # Track request
        http_requests_total.labels(
            method=method,
            endpoint=path,
            status=status
        ).inc()

        # Track duration
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method=method,
            endpoint=path
        ).observe(duration)

        return response

    except Exception as e:
        # Track error
        http_requests_total.labels(
            method=method,
            endpoint=path,
            status=500
        ).inc()

        errors_total.labels(
            error_type=type(e).__name__,
            endpoint=path
        ).inc()

        raise

    finally:
        http_requests_active.dec()


async def metrics_endpoint() -> FastAPIResponse:
    """Endpoint to expose Prometheus metrics."""
    metrics = generate_latest(registry)
    return FastAPIResponse(
        content=metrics,
        media_type=CONTENT_TYPE_LATEST
    )


# Helper functions for business metrics
def track_booking_created(status: str):
    """Track booking creation."""
    bookings_total.labels(status=status).inc()


def track_payment_processed(status: str):
    """Track payment processing."""
    payments_total.labels(status=status).inc()


def track_review_created():
    """Track review creation."""
    reviews_total.inc()


def track_attendance_marked(status: str):
    """Track attendance marking."""
    attendance_marked_total.labels(status=status).inc()


def update_db_connections(active: int, idle: int):
    """Update database connection pool metrics."""
    db_connections_active.set(active)
    db_connections_idle.set(idle)
