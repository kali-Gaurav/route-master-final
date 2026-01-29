# core/circuit_breaker.py
"""Circuit Breaker Pattern Implementation"""

import time
import asyncio
from enum import Enum
from typing import Callable, Any, Optional, Dict
import logging
import redis
import json

logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    def __init__(self, service_name: str, retry_after: int):
        self.service_name = service_name
        self.retry_after = retry_after
        super().__init__(f"Circuit breaker is open for {service_name}. Retry after {retry_after} seconds")

class CircuitBreaker:
    """Circuit breaker implementation with Redis persistence"""

    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Exception = Exception,
        redis_client: Optional[redis.Redis] = None
    ):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.redis = redis_client

        # In-memory state (fallback if Redis unavailable)
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._success_count = 0

        # Redis keys
        self._state_key = f"circuit_breaker:{service_name}:state"
        self._failure_key = f"circuit_breaker:{service_name}:failures"
        self._success_key = f"circuit_breaker:{service_name}:successes"

    def _load_state(self):
        """Load state from Redis"""
        if not self.redis:
            return

        try:
            state_data = self.redis.get(self._state_key)
            if state_data:
                state_info = json.loads(state_data)
                self._state = CircuitBreakerState(state_info['state'])
                self._failure_count = state_info.get('failure_count', 0)
                self._last_failure_time = state_info.get('last_failure_time')
                self._success_count = state_info.get('success_count', 0)
        except Exception as e:
            logger.warning(f"Failed to load circuit breaker state from Redis: {e}")

    def _save_state(self):
        """Save state to Redis"""
        if not self.redis:
            return

        try:
            state_info = {
                'state': self._state.value,
                'failure_count': self._failure_count,
                'last_failure_time': self._last_failure_time,
                'success_count': self._success_count,
                'updated_at': time.time()
            }
            self.redis.setex(self._state_key, 3600, json.dumps(state_info))  # 1 hour TTL
        except Exception as e:
            logger.warning(f"Failed to save circuit breaker state to Redis: {e}")

    @property
    def state(self) -> CircuitBreakerState:
        """Get current state"""
        self._load_state()
        return self._state

    def _can_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self._last_failure_time is None:
            return True
        return (time.time() - self._last_failure_time) >= self.recovery_timeout

    def _record_success(self):
        """Record successful call"""
        self._success_count += 1
        if self._state == CircuitBreakerState.HALF_OPEN:
            # If we're in half-open and had a success, close the circuit
            self._state = CircuitBreakerState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            logger.info(f"Circuit breaker for {self.service_name} closed after successful call")
        self._save_state()

    def _record_failure(self):
        """Record failed call"""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitBreakerState.HALF_OPEN:
            # If we're testing and it failed, go back to open
            self._state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker for {self.service_name} reopened after failed test")
        elif (self._state == CircuitBreakerState.CLOSED and
              self._failure_count >= self.failure_threshold):
            # If we hit the threshold, open the circuit
            self._state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker for {self.service_name} opened after {self._failure_count} failures")

        self._save_state()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        current_state = self.state

        if current_state == CircuitBreakerState.OPEN:
            if self._can_attempt_reset():
                self._state = CircuitBreakerState.HALF_OPEN
                self._save_state()
                logger.info(f"Circuit breaker for {self.service_name} entering half-open state")
            else:
                retry_after = int(self.recovery_timeout - (time.time() - (self._last_failure_time or 0)))
                raise CircuitBreakerOpenException(self.service_name, max(1, retry_after))

        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self._record_success()
            return result

        except self.expected_exception as e:
            self._record_failure()
            raise e
        except Exception as e:
            # For unexpected exceptions, also record as failure
            self._record_failure()
            raise e

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        self._load_state()
        return {
            'service_name': self.service_name,
            'state': self._state.value,
            'failure_count': self._failure_count,
            'success_count': self._success_count,
            'last_failure_time': self._last_failure_time,
            'can_attempt_reset': self._can_attempt_reset(),
            'failure_threshold': self.failure_threshold,
            'recovery_timeout': self.recovery_timeout
        }

class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.redis = redis_client

    def get_breaker(
        self,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Exception = Exception
    ) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self.breakers:
            self.breakers[service_name] = CircuitBreaker(
                service_name=service_name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                expected_exception=expected_exception,
                redis_client=self.redis
            )
        return self.breakers[service_name]

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {name: breaker.get_stats() for name, breaker in self.breakers.items()}

# Global registry instance
circuit_breaker_registry = None

def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Get global circuit breaker registry"""
    global circuit_breaker_registry
    if circuit_breaker_registry is None:
        # Try to get Redis client
        redis_client = None
        try:
            import redis
            from ..config import settings
            redis_client = redis.from_url(settings.redis_url)
        except:
            pass

        circuit_breaker_registry = CircuitBreakerRegistry(redis_client)

    return circuit_breaker_registry