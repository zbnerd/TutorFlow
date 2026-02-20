"""Audit middleware to extract actor and IP information from requests."""
from typing import Optional, Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Context variable for storing current request info
_request_context: dict = {}


def get_actor_id() -> Optional[int]:
    """Get current actor_id from request context."""
    return _request_context.get("actor_id")


def get_ip_address() -> Optional[str]:
    """Get current IP address from request context."""
    return _request_context.get("ip_address")


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and store audit context from requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and extract audit context."""
        # Extract IP address from request
        ip_address = self._get_client_ip(request)

        # Extract actor_id from JWT token (if authenticated)
        actor_id = self._extract_actor_id(request)

        # Store in context
        _request_context["actor_id"] = actor_id
        _request_context["ip_address"] = ip_address

        # Process request
        response = await call_next(request)

        # Clear context after request
        _request_context.clear()

        return response

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request headers."""
        # Check forwarded headers (for proxy/load balancer scenarios)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP from the list
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client address
        if request.client:
            return request.client.host

        return None

    def _extract_actor_id(self, request: Request) -> Optional[int]:
        """Extract actor_id from JWT token in request."""
        # This will be populated by the auth middleware
        # The JWT payload should contain user_id
        # For now, we'll check if the request state has user info
        if hasattr(request.state, "user_id"):
            return request.state.user_id

        # Alternative: check authorization header and decode JWT
        # This is a placeholder - actual implementation depends on your auth setup
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # Token would be decoded here by auth system
            # For now, return None - auth system will set request.state.user_id
            pass

        return None
