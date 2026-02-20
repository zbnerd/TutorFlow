"""Performance tracking middleware for TutorFlow API."""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from monitoring.prometheus.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_requests_active,
    errors_total,
)
from monitoring.logs.config import log_request, log_error


class PerformanceTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track request performance and logging."""

    def __init__(self, app: ASGIApp):
        """Initialize middleware."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track metrics."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()
        http_requests_active.inc()

        # Extract user info if available (from JWT when implemented)
        user_id = getattr(request.state, "user_id", None)

        method = request.method
        path = request.url.path

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            duration_sec = time.time() - start_time

            # Track metrics (exclude health/metrics endpoints)
            if not path.startswith("/health") and path != "/metrics":
                http_requests_total.labels(
                    method=method,
                    endpoint=path,
                    status=response.status_code,
                ).inc()

                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=path,
                ).observe(duration_sec)

            # Log request (skip health checks)
            if not path.startswith("/health"):
                log_request(
                    method=method,
                    path=path,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                    user_id=user_id,
                    request_id=request_id,
                )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration even for errors
            duration_ms = (time.time() - start_time) * 1000

            # Track error
            http_requests_total.labels(
                method=method,
                endpoint=path,
                status=500,
            ).inc()

            errors_total.labels(
                error_type=type(e).__name__,
                endpoint=path,
            ).inc()

            # Log error
            log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                endpoint=path,
                user_id=user_id,
                extra={"request_id": request_id, "duration_ms": duration_ms},
            )

            raise

        finally:
            http_requests_active.dec()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log detailed request information."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log incoming request details."""
        # Log request start
        from monitoring.logs.config import get_logger
        logger = get_logger("tutorflow.request")

        logger.debug(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
            }
        )

        return await call_next(request)
