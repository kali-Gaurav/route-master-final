# core/audit_middleware.py
"""Audit Middleware for Automatic Request Logging"""

import time
import json
from typing import Callable, Dict, Any, Optional
import logging

from .audit import AuditEvent, get_audit_service
from ..db_connection import get_db

logger = logging.getLogger(__name__)

class AuditMiddleware:
    """Middleware to automatically audit API requests"""

    def __init__(self, app):
        self.app = app
        self.exclude_paths = [
            "/health", "/ready", "/docs", "/redoc", "/openapi.json",
            "/metrics", "/favicon.ico"
        ]

    async def __call__(self, scope, receive, send):
        """ASGI middleware interface"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Check if request should be audited
        path = scope.get("path", "/")
        method = scope.get("method", "GET")

        if self._should_audit_request(path, method):
            # Extract request info for auditing
            user_id = self._extract_user_id_from_scope(scope)
            await self._audit_request_start(scope, user_id)

        # Continue with the request
        await self.app(scope, receive, send)

    def _should_audit_request(self, path: str, method: str) -> bool:
        """Determine if request should be audited"""
        # Skip excluded paths
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return False

        # Only audit state-changing operations and sensitive reads
        auditable_methods = ["POST", "PUT", "DELETE", "PATCH"]
        if method in auditable_methods:
            return True

        # Audit sensitive GET operations
        sensitive_get_paths = ["/users", "/admin", "/audit"]
        if method == "GET" and any(path.startswith(sensitive) for sensitive in sensitive_get_paths):
            return True

        return False

    async def _audit_request_start(self, scope, user_id):
        """Audit the start of a request"""
        try:
            path = scope.get("path", "/")
            method = scope.get("method", "GET")

            audit_service = get_audit_service()

            # Create audit event for request start
            audit_event = AuditEvent(
                user_id=user_id,
                action=f"{method} {path}",
                resource=path,
                ip_address=self._extract_ip_from_scope(scope),
                user_agent=self._extract_user_agent_from_scope(scope),
                method=method,
                endpoint=path,
                correlation_id=self._extract_correlation_id_from_scope(scope)
            )

            # Log audit event asynchronously
            await audit_service.log_event_async(audit_event)

        except Exception as e:
            logger.error(f"Failed to audit request start: {e}")

    def _extract_user_id_from_scope(self, scope) -> Optional[str]:
        """Extract user ID from ASGI scope"""
        # This is a simplified extraction - in a real app you'd decode JWT from headers
        headers = dict(scope.get("headers", []))
        auth_header = None
        for key, value in headers:
            if key == b"authorization":
                auth_header = value.decode()
                break

        if auth_header and auth_header.startswith("Bearer "):
            # In a real implementation, you'd decode the JWT to get user_id
            # For now, we'll return None as we can't decode without the full request context
            pass

        return None

    def _extract_ip_from_scope(self, scope) -> str:
        """Extract client IP from ASGI scope"""
        # Try X-Forwarded-For header first (for proxies)
        headers = dict(scope.get("headers", []))
        for key, value in headers:
            if key == b"x-forwarded-for":
                return value.decode().split(",")[0].strip()
            elif key == b"x-real-ip":
                return value.decode()

        # Fallback to direct client
        client = scope.get("client")
        if client:
            return client[0]
        return "unknown"

    def _extract_user_agent_from_scope(self, scope) -> str:
        """Extract user agent from ASGI scope"""
        headers = dict(scope.get("headers", []))
        for key, value in headers:
            if key == b"user-agent":
                return value.decode()
        return "unknown"

    def _extract_correlation_id_from_scope(self, scope) -> Optional[str]:
        """Extract correlation ID from ASGI scope"""
        headers = dict(scope.get("headers", []))
        for key, value in headers:
            if key == b"x-correlation-id":
                return value.decode()
        return None