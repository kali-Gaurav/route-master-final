# tests/test_security_features.py
"""Comprehensive tests for security features"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from backend.core.password_policy import PasswordPolicyValidator, PasswordPolicyViolation
from backend.core.csrf import CSRFProtection
from backend.core.rate_limiting import AdvancedRateLimitMiddleware, RateLimiter
from backend.core.audit import AuditService, AuditEvent
from backend.core.email_service import EmailService, EmailVerificationToken
from backend.core.circuit_breaker import CircuitBreaker, CircuitBreakerRegistry, CircuitBreakerState, CircuitBreakerOpenException

class TestPasswordPolicy:
    """Test password policy validation"""

    def setup_method(self):
        self.validator = PasswordPolicyValidator()

    def test_valid_password(self):
        """Test valid password passes all checks"""
        result = self.validator.validate_password("MySecurePass123!")
        assert result['valid'] is True
        assert result['strength'] == 'very_strong'
        assert result['score'] == 4

    def test_weak_password_violations(self):
        """Test weak password fails multiple checks"""
        result = self.validator.validate_password("password")
        assert result['valid'] is False
        assert len(result['violations']) >= 3
        assert "Password must contain at least one uppercase letter" in result['violations']

    def test_personal_info_detection(self):
        """Test personal information detection"""
        user_info = {'username': 'john', 'email': 'john@example.com'}
        result = self.validator.validate_password('john123', user_info)
        assert result['valid'] is False

    def test_common_password_rejection(self):
        """Test common password rejection"""
        result = self.validator.validate_password('password123')
        assert result['valid'] is False
        assert any('easily guessable' in v for v in result['violations'])

    def test_consecutive_chars_detection(self):
        """Test consecutive identical characters detection"""
        result = self.validator.validate_password('MyPasssssssword123!')
        assert result['valid'] is False
        assert any('consecutive identical characters' in v for v in result['violations'])

    def test_policy_requirements_format(self):
        """Test policy requirements structure"""
        requirements = self.validator.get_policy_requirements()
        required_keys = ['min_length', 'require_uppercase', 'require_digits', 'require_special_chars']
        for key in required_keys:
            assert key in requirements

class TestCSRFProtection:
    """Test CSRF protection"""

    def setup_method(self):
        self.csrf = CSRFProtection(secret_key="test-secret-key")

    def test_generate_and_validate_token(self):
        """Test token generation and validation"""
        session_id = "test-session-123"
        token = self.csrf.generate_token(session_id)

        assert self.csrf.validate_token(token, session_id) is True
        assert self.csrf.validate_token(token, "wrong-session") is False
        assert self.csrf.validate_token("invalid-token", session_id) is False

    def test_token_tampering_detection(self):
        """Test detection of tampered tokens"""
        session_id = "test-session-123"
        token = self.csrf.generate_token(session_id)

        # Tamper with token
        tampered_token = token.replace("a", "b") if "a" in token else token + "x"
        assert self.csrf.validate_token(tampered_token, session_id) is False

class TestRateLimiting:
    """Test advanced rate limiting"""

    def setup_method(self):
        self.limiter = RateLimiter()

    @pytest.mark.asyncio
    async def test_fixed_window_rate_limiting(self):
        """Test fixed window rate limiting"""
        identifier = "test-user"
        endpoint = "/api/test"

        # First 5 requests should succeed
        for i in range(5):
            allowed, remaining, retry_after = await self.limiter.check_fixed_window(
                identifier, endpoint, 5, 60
            )
            assert allowed is True
            assert remaining == 4 - i

        # 6th request should fail
        allowed, remaining, retry_after = await self.limiter.check_fixed_window(
            identifier, endpoint, 5, 60
        )
        assert allowed is False
        assert remaining == 0
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_sliding_window_rate_limiting(self):
        """Test sliding window rate limiting"""
        identifier = "test-user"
        endpoint = "/api/test"

        # Should allow requests within limit
        for i in range(3):
            allowed, remaining, retry_after = await self.limiter.check_sliding_window(
                identifier, endpoint, 3, 60
            )
            assert allowed is True

        # Next request should be blocked
        allowed, remaining, retry_after = await self.limiter.check_sliding_window(
            identifier, endpoint, 3, 60
        )
        assert allowed is False

class TestAuditSystem:
    """Test audit logging system"""

    def setup_method(self):
        self.db = Mock()
        self.audit_service = AuditService(self.db)

    @pytest.mark.asyncio
    async def test_audit_event_creation(self):
        """Test audit event creation and logging"""
        event = AuditEvent(
            user_id="user-123",
            action="login",
            resource_type="authentication",
            method="POST",
            endpoint="/auth/login",
            status_code=200,
            duration_ms=150
        )

        await self.audit_service.log_event(event)

        # Verify database interaction
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_audit_data_sanitization(self):
        """Test sensitive data sanitization in audit logs"""
        event = AuditEvent(
            user_id="user-123",
            action="update",
            resource_type="user",
            method="PUT",
            endpoint="/users/profile",
            request_data={
                "password": "secret123",
                "email": "user@example.com",
                "api_key": "sk-123456",
                "normal_field": "normal_value"
            }
        )

        sanitized = event._sanitize_data(event.request_data)

        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["email"] == "user@example.com"
        assert sanitized["normal_field"] == "normal_value"

class TestEmailService:
    """Test email service functionality"""

    def setup_method(self):
        self.email_config = Mock()
        self.email_config.smtp_server = "smtp.test.com"
        self.email_config.smtp_port = 587
        self.email_config.from_email = "test@example.com"
        self.email_config.from_name = "Test App"

        # Mock Redis for testing
        self.mock_redis = Mock()
        self.email_service = EmailService(self.email_config, self.mock_redis)

    def test_token_generation_and_verification(self):
        """Test email verification token generation and verification"""
        email = "test@example.com"

        # Mock Redis storage
        stored_data = None
        def mock_setex(key, expiry, data):
            nonlocal stored_data
            stored_data = data

        def mock_get(key):
            return stored_data

        def mock_delete(key):
            nonlocal stored_data
            stored_data = None

        self.mock_redis.setex = mock_setex
        self.mock_redis.get = mock_get
        self.mock_redis.delete = mock_delete

        token = self.email_service.token_manager.generate_token(email)

        assert token is not None
        assert len(token) >= 32  # Token should be reasonably long (at least 32 chars)

        # Verify token
        verified_email = self.email_service.verify_email_token(token)
        assert verified_email == email

        # Token should be consumed (one-time use)
        second_verification = self.email_service.verify_email_token(token)
        assert second_verification is None

    @patch('smtplib.SMTP')
    def test_send_verification_email(self, mock_smtp):
        """Test verification email sending"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = self.email_service.send_verification_email(
            "test@example.com",
            "https://app.com/verify"
        )

        assert result is True
        mock_server.sendmail.assert_called_once()

class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    def setup_method(self):
        self.breaker = CircuitBreaker("test-service", failure_threshold=3, recovery_timeout=1)

    @pytest.mark.asyncio
    async def test_circuit_breaker_success(self):
        """Test successful calls keep circuit closed"""
        async def success_func():
            return "success"

        result = await self.breaker.call(success_func)
        assert result == "success"
        assert self.breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_threshold(self):
        """Test circuit opens after failure threshold"""
        async def failing_func():
            raise ValueError("Test error")

        # First few failures should keep circuit closed
        for i in range(2):
            with pytest.raises(ValueError):
                await self.breaker.call(failing_func)
        assert self.breaker.state == CircuitBreakerState.CLOSED

        # Third failure should open circuit
        with pytest.raises(ValueError):
            await self.breaker.call(failing_func)
        assert self.breaker.state == CircuitBreakerState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery"""
        async def failing_func():
            raise ValueError("Test error")

        async def success_func():
            return "success"

        # Open the circuit
        for i in range(3):
            with pytest.raises(ValueError):
                await self.breaker.call(failing_func)
        assert self.breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Next call should be in half-open state and succeed
        result = await self.breaker.call(success_func)
        assert result == "success"
        assert self.breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_open_exception(self):
        """Test circuit breaker open exception"""
        async def failing_func():
            raise ValueError("Test error")

        # Open the circuit
        for i in range(3):
            with pytest.raises(ValueError):
                await self.breaker.call(failing_func)

        # Next call should raise CircuitBreakerOpenException
        with pytest.raises(CircuitBreakerOpenException) as exc_info:
            await self.breaker.call(failing_func)

        assert exc_info.value.service_name == "test-service"
        assert exc_info.value.retry_after > 0

class TestSecurityIntegration:
    """Integration tests for security features"""

    @pytest.mark.asyncio
    async def test_comprehensive_password_validation(self):
        """Test comprehensive password validation with edge cases"""
        validator = PasswordPolicyValidator()

        test_cases = [
            # (password, expected_valid, min_violations)
            ("", False, 2),  # Too short, missing requirements
            ("a", False, 4),  # Too short, missing all requirements
            ("password", False, 3),  # Common password, missing requirements
            ("Password", False, 2),  # Missing digits and special chars
            ("Password1", False, 1),  # Missing special chars
            ("Password1!", True, 0),  # Valid password
            ("MySecurePass123!", True, 0),  # Very secure password
            ("P@ssw0rd123", True, 0),  # Valid with various chars
        ]

        for password, expected_valid, min_violations in test_cases:
            result = validator.validate_password(password)
            assert result['valid'] == expected_valid, f"Failed for password: {password}"
            if not expected_valid:
                assert len(result['violations']) >= min_violations, f"Insufficient violations for: {password}"

    def test_csrf_token_integrity(self):
        """Test CSRF token integrity across different sessions"""
        csrf = CSRFProtection(secret_key="test-secret")

        # Generate tokens for different sessions
        token1 = csrf.generate_token("session1")
        token2 = csrf.generate_token("session2")

        # Tokens should be different
        assert token1 != token2

        # Each token should only validate for its session
        assert csrf.validate_token(token1, "session1") is True
        assert csrf.validate_token(token1, "session2") is False
        assert csrf.validate_token(token2, "session1") is False
        assert csrf.validate_token(token2, "session2") is True

    @pytest.mark.asyncio
    async def test_rate_limiting_edge_cases(self):
        """Test rate limiting edge cases"""
        limiter = RateLimiter()

        # Test with very short window
        allowed, remaining, retry_after = await limiter.check_fixed_window(
            "user1", "/api/test", 2, 1  # 2 requests per 1 second
        )
        assert allowed is True
        assert remaining == 1

        # Immediate second request should succeed
        allowed, remaining, retry_after = await limiter.check_fixed_window(
            "user1", "/api/test", 2, 1
        )
        assert allowed is True
        assert remaining == 0

        # Third request should fail
        allowed, remaining, retry_after = await limiter.check_fixed_window(
            "user1", "/api/test", 2, 1
        )
        assert allowed is False
        assert remaining == 0

    def test_audit_event_serialization(self):
        """Test audit event data serialization"""
        event = AuditEvent(
            user_id="user-123",
            action="create",
            resource_type="route",
            method="POST",
            endpoint="/api/routes",
            request_data={"name": "Test Route", "distance": 100},
            status_code=201,
            duration_ms=250
        )

        event_dict = event.to_dict()

        assert event_dict['user_id'] == "user-123"
        assert event_dict['action'] == "create"
        assert event_dict['resource_type'] == "route"
        assert event_dict['status_code'] == 201
        assert event_dict['duration_ms'] == 250
        assert 'timestamp' in event_dict

    @pytest.mark.asyncio
    async def test_circuit_breaker_state_transitions(self):
        """Test all circuit breaker state transitions"""
        breaker = CircuitBreaker("test-service", failure_threshold=2, recovery_timeout=1)

        async def success_func():
            return "ok"

        async def failure_func():
            raise ConnectionError("Service unavailable")

        # Start in closed state
        assert breaker.state == CircuitBreakerState.CLOSED

        # Success keeps it closed
        result = await breaker.call(success_func)
        assert result == "ok"
        assert breaker.state == CircuitBreakerState.CLOSED

        # Failures lead to open state
        for i in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(failure_func)

        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Next call should succeed and close circuit
        result = await breaker.call(success_func)
        assert result == "ok"
        assert breaker.state == CircuitBreakerState.CLOSED

        # More failures should reopen circuit
        for i in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(failure_func)

        assert breaker.state == CircuitBreakerState.OPEN