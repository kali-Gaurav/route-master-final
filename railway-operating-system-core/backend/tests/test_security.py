# tests/test_security.py
import pytest
from backend.core.security import (
    verify_password, get_password_hash, create_access_token, verify_token
)
from backend.config import settings

class TestPasswordSecurity:
    """Test password hashing and verification"""

    def test_password_hashing(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) == True
        assert verify_password("wrongpassword", hashed) == False

    def test_password_verification_edge_cases(self):
        """Test password verification with edge cases"""
        # Empty password
        hashed = get_password_hash("")
        assert verify_password("", hashed) == True

        # Long password
        long_password = "a" * 1000
        hashed = get_password_hash(long_password)
        assert verify_password(long_password, hashed) == True

class TestJWTToken:
    """Test JWT token creation and verification"""

    def test_token_creation(self):
        """Test JWT token creation"""
        data = {"sub": "test@example.com", "role": "user"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)

    def test_token_verification(self):
        """Test JWT token verification"""
        data = {"sub": "test@example.com", "role": "user"}
        token = create_access_token(data)

        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert payload["role"] == "user"

    def test_invalid_token_verification(self):
        """Test verification of invalid tokens"""
        assert verify_token("invalid.token.here") is None
        assert verify_token("") is None
        assert verify_token("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImp0aSI6ImQ5YjQ5N2E5LTc4NTMtNDI4ZS1iMzI5LWIzZjEwZjVhMzE4ZSIsImlhdCI6MTY4MzY5MzYwMCwiZXhwIjoxNjgzNjk3MjAwfQ.invalid") is None

    def test_token_expiration(self):
        """Test token expiration"""
        import time
        from datetime import timedelta

        # Create token that expires immediately
        data = {"sub": "test@example.com"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        # Wait a bit
        time.sleep(0.1)

        payload = verify_token(token)
        assert payload is None  # Should be expired

class TestSecurityIntegration:
    """Test security functions integration"""

    def test_full_authentication_flow(self):
        """Test complete authentication flow"""
        # Hash password
        password = "securepassword123"
        hashed = get_password_hash(password)

        # Verify password
        assert verify_password(password, hashed)

        # Create token
        user_data = {"sub": "user@example.com", "role": "admin", "tenant_id": "123"}
        token = create_access_token(user_data)

        # Verify token
        payload = verify_token(token)
        assert payload["sub"] == "user@example.com"
        assert payload["role"] == "admin"