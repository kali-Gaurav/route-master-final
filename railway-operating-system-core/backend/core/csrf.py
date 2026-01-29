# core/csrf.py
"""CSRF Protection Middleware"""

import secrets
import hashlib
import hmac
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class CSRFProtection:
    """CSRF protection using double-submit cookie pattern"""

    def __init__(self, secret_key: str, cookie_name: str = "csrf_token", header_name: str = "X-CSRF-Token"):
        self.secret_key = secret_key
        self.cookie_name = cookie_name
        self.header_name = header_name

    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token for session"""
        # Create token as HMAC of session_id
        token_data = f"{session_id}:{secrets.token_hex(32)}"
        signature = hmac.new(
            self.secret_key.encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"{token_data}:{signature}"

    def validate_token(self, token: str, session_id: str) -> bool:
        """Validate CSRF token"""
        try:
            token_data, signature = token.rsplit(":", 1)
            expected_signature = hmac.new(
                self.secret_key.encode(),
                token_data.encode(),
                hashlib.sha256
            ).hexdigest()

            # Verify signature and session_id match
            if not hmac.compare_digest(signature, expected_signature):
                return False

            # Extract session_id from token
            token_session_id = token_data.split(":")[0]
            return token_session_id == session_id

        except (ValueError, IndexError):
            return False

    def get_token_from_request(self, request: Request) -> Optional[str]:
        """Extract CSRF token from request"""
        # Check header first
        token = request.headers.get(self.header_name)
        if token:
            return token

        # Check form data
        if hasattr(request, 'form') and request.form:
            token = request.form.get(self.header_name.lower().replace('-', '_'))
            if token:
                return token

        # Check JSON body
        if hasattr(request, 'json') and request.json:
            try:
                body = request.json()
                token = body.get(self.header_name.lower().replace('-', '_'))
                if token:
                    return token
            except:
                pass

        return None

    def get_session_id(self, request: Request) -> str:
        """Get session ID from request (using user ID or IP + user agent)"""
        # In a real app, this would be the actual session ID
        # For now, use a combination of IP and user agent
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")

        return f"{client_ip}:{user_agent}"

class CSRFMiddleware:
    """FastAPI middleware for CSRF protection"""

    def __init__(self, csrf_protection: CSRFProtection, exclude_paths: list = None):
        self.csrf = csrf_protection
        self.exclude_paths = exclude_paths or ["/health", "/ready", "/docs", "/redoc", "/openapi.json"]

    async def __call__(self, request: Request, call_next):
        # Skip CSRF check for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            response = await call_next(request)
            # Add CSRF token to response for GET requests
            if request.method == "GET":
                session_id = self.csrf.get_session_id(request)
                csrf_token = self.csrf.generate_token(session_id)
                response.set_cookie(
                    self.csrf.cookie_name,
                    csrf_token,
                    httponly=False,  # Allow JavaScript access
                    secure=True,
                    samesite="strict"
                )
            return response

        # Skip CSRF check for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Check CSRF token for state-changing methods
        session_id = self.csrf.get_session_id(request)
        token = self.csrf.get_token_from_request(request)

        if not token:
            logger.warning(f"CSRF token missing for {request.method} {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "CSRF token required"}
            )

        if not self.csrf.validate_token(token, session_id):
            logger.warning(f"CSRF token validation failed for {request.method} {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "CSRF token invalid"}
            )

        return await call_next(request)