# connection.py - Enhanced Database Connection Management
import time
import logging
import os
from contextlib import contextmanager
from typing import Optional, Generator, Any
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, DisconnectionError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration."""
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '5432'))
        self.database = os.getenv('DB_NAME', 'railway_os')
        self.username = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'password')
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '20'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '30'))
        self.pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))
        self.pool_pre_ping = os.getenv('DB_POOL_PRE_PING', 'true').lower() == 'true'
        self.enable_query_logging = os.getenv('DB_ENABLE_QUERY_LOGGING', 'false').lower() == 'true'
        self.database_url = os.getenv('DATABASE_URL', self.connection_string)
        self.read_replica_url = os.getenv('DB_READ_REPLICA_URL', '')
        self.enable_performance_monitoring = os.getenv('DB_ENABLE_PERF_MONITORING', 'true').lower() == 'true'
        self.slow_query_threshold = float(os.getenv('DB_SLOW_QUERY_THRESHOLD', '1.0'))
        self.health_check_interval = int(os.getenv('DB_HEALTH_CHECK_INTERVAL', '60'))
        self.max_retries = int(os.getenv('DB_MAX_RETRIES', '3'))
        self.retry_delay = float(os.getenv('DB_RETRY_DELAY', '0.5'))
        self.retry_backoff = float(os.getenv('DB_RETRY_BACKOFF', '2.0'))

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def validate_config(self) -> list:
        """Validate configuration parameters."""
        issues = []
        if not self.host:
            issues.append("Host is required")
        if not self.database:
            issues.append("Database name is required")
        if not self.username:
            issues.append("Username is required")
        if self.port <= 0 or self.port > 65535:
            issues.append("Invalid port number")
        if self.pool_size <= 0:
            issues.append("Pool size must be positive")
        return issues

class DatabaseConnectionManager:
    """Enhanced database connection manager with all required features."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine: Optional[Engine] = None
        self._read_engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._health_check_timestamp = 0
        self._connection_healthy = False

        # Validate configuration
        issues = config.validate_config()
        if issues:
            raise ValueError(f"Configuration validation failed: {issues}")

        self._initialize_engines()

    def _initialize_engines(self):
        """Initialize database engines with all required features."""
        # Main engine configuration
        engine_kwargs = {
            'poolclass': QueuePool,
            'pool_size': self.config.pool_size,
            'max_overflow': self.config.max_overflow,
            'pool_timeout': self.config.pool_timeout,
            'pool_recycle': self.config.pool_recycle,
            'pool_pre_ping': self.config.pool_pre_ping,
            'echo': self.config.enable_query_logging,
        }

        # Create main engine
        self._engine = create_engine(self.config.database_url, **engine_kwargs)

        # Create read replica engine if configured
        if self.config.read_replica_url:
            self._read_engine = create_engine(self.config.read_replica_url, **engine_kwargs)

        # Configure engine events for monitoring
        self._configure_engine_events()

        # Create session factory
        self._session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine
        )

        logger.info("Database engines initialized successfully")

    def _configure_engine_events(self):
        """Configure SQLAlchemy engine events for monitoring and optimization."""
        @event.listens_for(self._engine, "connect")
        def connect(dbapi_connection, connection_record):
            logger.debug("Database connection established")
            # Set connection-specific parameters
            cursor = dbapi_connection.cursor()
            cursor.execute("SET timezone = 'UTC';")
            cursor.execute(f"SET work_mem = '64MB';")  # Optimize memory for complex queries
            cursor.close()

        @event.listens_for(self._engine, "checkout")
        def checkout(dbapi_connection, connection_record, connection_proxy):
            logger.debug("Database connection checked out from pool")

        @event.listens_for(self._engine, "checkin")
        def checkin(dbapi_connection, connection_record):
            logger.debug("Database connection returned to pool")

        @event.listens_for(self._engine, "before_execute")
        def before_execute(conn, clauseelement, multiparams, params):
            if self.config.enable_performance_monitoring:
                conn.info.setdefault('query_start_time', []).append(time.time())

        @event.listens_for(self._engine, "after_execute")
        def after_execute(conn, clauseelement, multiparams, params, result):
            if self.config.enable_performance_monitoring:
                start_time = conn.info['query_start_time'].pop()
                duration = time.time() - start_time

                if duration > self.config.slow_query_threshold:
                    logger.warning(f"Slow query detected: {duration:.2f}s - {str(clauseelement)}")

    def get_session(self) -> Session:
        """Get a database session with automatic cleanup."""
        return self._session_factory()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Context manager for database sessions with automatic commit/rollback."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            session.close()

    def health_check(self) -> dict[str, Any]:
        """Comprehensive database health check."""
        current_time = time.time()

        # Cache health check results
        if current_time - self._health_check_timestamp < self.config.health_check_interval:
            return {
                'healthy': self._connection_healthy,
                'cached': True,
                'timestamp': self._health_check_timestamp
            }

        try:
            with self.session_scope() as session:
                # Test basic connectivity
                result = session.execute(text("SELECT 1 as test"))
                test_value = result.fetchone()[0]

                # Test table existence
                result = session.execute(text("""
                    SELECT COUNT(*) as table_count
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """))
                table_count = result.fetchone()[0]

                # Test connection pool status
                pool_status = {
                    'pool_size': self.config.pool_size,
                    'checked_out': self._engine.pool.checkedout(),
                    'overflow': self._engine.pool._overflow,
                }

                # Test query performance
                start_time = time.time()
                session.execute(text("SELECT COUNT(*) FROM stations LIMIT 1"))
                query_time = time.time() - start_time

                self._connection_healthy = True
                self._health_check_timestamp = current_time

                return {
                    'healthy': True,
                    'cached': False,
                    'timestamp': current_time,
                    'connection_test': test_value == 1,
                    'table_count': table_count,
                    'pool_status': pool_status,
                    'query_performance_ms': query_time * 1000,
                    'database_size': self._get_database_size(session),
                    'active_connections': self._get_active_connections(session),
                }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self._connection_healthy = False
            self._health_check_timestamp = current_time

            return {
                'healthy': False,
                'cached': False,
                'timestamp': current_time,
                'error': str(e)
            }

    def _get_database_size(self, session: Session) -> str:
        """Get database size information."""
        try:
            result = session.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """))
            return result.fetchone()[0]
        except:
            return "Unknown"

    def _get_active_connections(self, session: Session) -> int:
        """Get count of active connections."""
        try:
            result = session.execute(text("""
                SELECT COUNT(*) as active_connections
                FROM pg_stat_activity
                WHERE state = 'active'
            """))
            return result.fetchone()[0]
        except:
            return 0

    def execute_with_retry(self, operation, *args, **kwargs):
        """Execute database operation with retry logic."""
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except (OperationalError, DisconnectionError) as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (self.config.retry_backoff ** attempt)
                    logger.warning(f"Database operation failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"Database operation failed after {self.config.max_retries + 1} attempts: {e}")

        raise last_exception

    def get_read_session(self) -> Optional[Session]:
        """Get a read-only session (uses replica if available)."""
        if self._read_engine:
            return sessionmaker(autocommit=False, autoflush=False, bind=self._read_engine)()
        return self.get_session()

    def dispose(self):
        """Dispose of database engines."""
        if self._engine:
            self._engine.dispose()
        if self._read_engine:
            self._read_engine.dispose()
        logger.info("Database engines disposed")

# Global connection manager instance
config = DatabaseConfig()
db_manager = DatabaseConnectionManager(config)

# Backward compatibility
engine = db_manager._engine
SessionLocal = db_manager._session_factory
from .base import Base

def get_db() -> Generator[Session, None, None]:
    """Get database session (backward compatibility)."""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()

def get_read_db() -> Generator[Session, None, None]:
    """Get read-only database session."""
    db = db_manager.get_read_session()
    try:
        yield db
    finally:
        db.close()