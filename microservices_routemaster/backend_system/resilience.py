"""
Circuit Breaker Pattern Implementation
For resilient service-to-service communication
"""

from enum import Enum
from datetime import datetime, timedelta
import logging
from typing import Callable, Any
import functools
import time

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Failing, reject requests
    HALF_OPEN = "half_open"    # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation
    
    Prevents cascading failures by failing fast
    """
    
    def __init__(self,
                 name: str,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: Exception = Exception):
        """
        Initialize circuit breaker
        
        Args:
            name: Circuit breaker name
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds before trying to recover (half-open)
            expected_exception: Exception type to catch
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.last_state_change = datetime.utcnow()
        
        # Metrics
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker
        
        Args:
            func: Function to call
            args: Positional arguments
            kwargs: Keyword arguments
        
        Returns:
            Function result
        
        Raises:
            CircuitBreakerOpen: If circuit is open
        """
        self.total_requests += 1
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"[{self.name}] Circuit breaker entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpen(f"Circuit breaker {self.name} is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful request"""
        self.total_successes += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self._close()
        elif self.failure_count > 0:
            self.failure_count -= 1
    
    def _on_failure(self):
        """Handle failed request"""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        logger.warning(f"[{self.name}] Failure {self.failure_count}/{self.failure_threshold}")
        
        if self.failure_count >= self.failure_threshold:
            self._open()
    
    def _open(self):
        """Open the circuit"""
        if self.state != CircuitState.OPEN:
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.utcnow()
            logger.error(f"[{self.name}] Circuit breaker OPEN (failing fast)")
    
    def _close(self):
        """Close the circuit"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = datetime.utcnow()
        logger.info(f"[{self.name}] Circuit breaker CLOSED (recovered)")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time passed to attempt recovery"""
        if not self.last_failure_time:
            return False
        
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def get_metrics(self) -> dict:
        """Get circuit breaker metrics"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'total_requests': self.total_requests,
            'total_failures': self.total_failures,
            'total_successes': self.total_successes,
            'failure_rate': (
                self.total_failures / self.total_requests 
                if self.total_requests > 0 else 0
            ),
            'last_state_change': self.last_state_change.isoformat()
        }


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit is open"""
    pass


class CircuitBreakerDecorator:
    """Decorator for circuit breaker pattern"""
    
    _breakers = {}
    
    @classmethod
    def circuit_breaker(cls, name: str = None, failure_threshold: int = 5):
        """
        Decorator to add circuit breaker to function
        
        Usage:
            @CircuitBreakerDecorator.circuit_breaker('route-service', failure_threshold=3)
            def call_route_service():
                pass
        """
        def decorator(func):
            breaker_name = name or f"{func.__module__}.{func.__name__}"
            
            if breaker_name not in cls._breakers:
                cls._breakers[breaker_name] = CircuitBreaker(
                    breaker_name,
                    failure_threshold=failure_threshold
                )
            
            breaker = cls._breakers[breaker_name]
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return breaker.call(func, *args, **kwargs)
            
            wrapper.breaker = breaker
            return wrapper
        
        return decorator
    
    @classmethod
    def get_breaker(cls, name: str) -> CircuitBreaker:
        """Get circuit breaker by name"""
        return cls._breakers.get(name)
    
    @classmethod
    def get_all_breakers(cls) -> dict:
        """Get all circuit breakers"""
        return cls._breakers


class BulkheadPattern:
    """
    Bulkhead pattern - isolate resources
    Prevents one service's failures from bringing down others
    """
    
    def __init__(self, name: str, pool_size: int, queue_timeout: int = 30):
        """
        Initialize bulkhead
        
        Args:
            name: Bulkhead name
            pool_size: Number of concurrent requests allowed
            queue_timeout: Timeout for acquiring slot (seconds)
        """
        self.name = name
        self.pool_size = pool_size
        self.queue_timeout = queue_timeout
        
        # In production: use actual semaphore/queue
        self.active_count = 0
    
    def acquire(self, timeout: int = None) -> bool:
        """Try to acquire a slot"""
        if self.active_count >= self.pool_size:
            logger.warning(f"[{self.name}] Bulkhead full ({self.active_count}/{self.pool_size})")
            return False
        
        self.active_count += 1
        return True
    
    def release(self):
        """Release a slot"""
        if self.active_count > 0:
            self.active_count -= 1


class RetryPolicy:
    """
    Retry policy with exponential backoff
    
    Only retries on transient failures (idempotent operations)
    """
    
    def __init__(self, 
                 max_retries: int = 3,
                 backoff_factor: float = 2.0,
                 jitter: bool = True):
        """
        Initialize retry policy
        
        Args:
            max_retries: Maximum number of retries
            backoff_factor: Exponential backoff factor
            jitter: Add random jitter to backoff
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Function to call
            args: Positional arguments
            kwargs: Keyword arguments
        
        Returns:
            Function result
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    wait_time = self._calculate_backoff(attempt)
                    logger.info(f"Retry {attempt}/{self.max_retries}, waiting {wait_time:.2f}s")
                    time.sleep(wait_time)
                
                return func(*args, **kwargs)
            
            except Exception as e:
                if not self._should_retry(e, attempt):
                    raise
                
                last_exception = e
                logger.warning(f"Attempt {attempt+1} failed: {e}")
        
        raise last_exception
    
    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter"""
        backoff = self.backoff_factor ** attempt
        
        if self.jitter:
            import random
            jitter = random.random() * 0.1 * backoff
            backoff += jitter
        
        return backoff
    
    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if exception should be retried"""
        
        # Don't retry client errors (4xx)
        if hasattr(exception, 'status_code'):
            if 400 <= exception.status_code < 500:
                return False
        
        # Don't retry on last attempt
        if attempt >= self.max_retries:
            return False
        
        # Retry on transient failures
        transient_errors = [
            'ConnectionError',
            'Timeout',
            'TimeoutError',
            'ConnectionRefusedError',
            'ConnectionResetError'
        ]
        
        error_name = exception.__class__.__name__
        return any(err in error_name for err in transient_errors)
