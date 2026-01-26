"""
Production Data Pipeline Configuration

Central configuration management for the entire system.
Supports multiple environments: local, staging, production.
"""

import os
from pathlib import Path
from typing import Optional
from enum import Enum
from dataclasses import dataclass


class Environment(Enum):
    """Environment types"""
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    # SQLite for local, PostgreSQL for production
    type: str = "sqlite"  # sqlite, postgresql
    
    # SQLite path
    sqlite_path: str = "data/production.db"
    
    # PostgreSQL settings
    postgresql_host: str = "localhost"
    postgresql_port: int = 5432
    postgresql_user: str = "railway"
    postgresql_password: str = "password"
    postgresql_database: str = "route_master"
    
    # Connection pool
    pool_size: int = 20
    max_overflow: int = 40
    pool_recycle: int = 3600
    
    # Performance
    echo_sql: bool = False
    
    @property
    def connection_string(self) -> str:
        """Get connection string"""
        if self.type == "sqlite":
            return f"sqlite:///{self.sqlite_path}"
        elif self.type == "postgresql":
            return (
                f"postgresql://{self.postgresql_user}:"
                f"{self.postgresql_password}@"
                f"{self.postgresql_host}:{self.postgresql_port}/"
                f"{self.postgresql_database}"
            )
        else:
            raise ValueError(f"Unknown database type: {self.type}")


@dataclass
class IngestionConfig:
    """Data ingestion configuration"""
    # RAPPID API
    rappid_api_base: str = "https://api.railways.example.com"
    rappid_api_key: str = "YOUR_API_KEY"
    rappid_api_timeout: int = 30
    
    # Rate limiting (requests per second)
    rate_limit_rps: int = 10
    
    # Caching
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    cache_dir: str = "data/cache"
    
    # Retry logic
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    
    # Batch processing
    batch_size: int = 100
    
    # Background jobs
    daily_refresh_hour: int = 2  # 2 AM
    refresh_interval_minutes: int = 60


@dataclass
class APIConfig:
    """API configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # API settings
    api_version: str = "v1"
    
    # Request validation
    max_request_size_mb: int = 10
    request_timeout_seconds: int = 30
    
    # Rate limiting
    requests_per_minute: int = 300
    
    # CORS
    cors_origins: list = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_dir: str = "logs"
    
    # File logging
    log_file: str = "production.log"
    max_log_size_mb: int = 100
    backup_count: int = 10
    
    # Structured logging
    use_json_logging: bool = True


@dataclass
class MetricsConfig:
    """Metrics configuration"""
    enabled: bool = True
    
    # Storage
    metrics_db_path: str = "data/metrics.db"
    
    # Collection
    collection_interval_seconds: int = 60
    
    # Retention
    retention_days: int = 30


@dataclass
class SystemConfig:
    """Complete system configuration"""
    environment: Environment = Environment.LOCAL
    
    # Components
    database: DatabaseConfig = None
    ingestion: IngestionConfig = None
    api: APIConfig = None
    logging: LoggingConfig = None
    metrics: MetricsConfig = None
    
    # Paths
    data_dir: str = "data"
    cache_dir: str = "data/cache"
    logs_dir: str = "logs"
    
    # System settings
    debug: bool = False
    
    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig()
        if self.ingestion is None:
            self.ingestion = IngestionConfig()
        if self.api is None:
            self.api = APIConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.metrics is None:
            self.metrics = MetricsConfig()
    
    @classmethod
    def from_environment(cls, env: Optional[str] = None) -> "SystemConfig":
        """Load configuration from environment"""
        env_str = env or os.getenv("ENVIRONMENT", "local").lower()
        
        try:
            environment = Environment(env_str)
        except ValueError:
            environment = Environment.LOCAL
        
        config = cls(environment=environment)
        
        # Override with environment variables
        if os.getenv("DATABASE_TYPE"):
            config.database.type = os.getenv("DATABASE_TYPE")
        if os.getenv("DATABASE_URL"):
            # Handle custom database URL
            pass
        
        if os.getenv("RAPPID_API_KEY"):
            config.ingestion.rappid_api_key = os.getenv("RAPPID_API_KEY")
        
        if os.getenv("API_HOST"):
            config.api.host = os.getenv("API_HOST")
        if os.getenv("API_PORT"):
            config.api.port = int(os.getenv("API_PORT"))
        
        if os.getenv("LOG_LEVEL"):
            try:
                config.logging.level = LogLevel(os.getenv("LOG_LEVEL"))
            except ValueError:
                pass
        
        # Set debug mode
        config.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        return config
    
    def create_directories(self):
        """Create necessary directories"""
        dirs = [
            self.data_dir,
            self.cache_dir,
            self.logs_dir,
            self.ingestion.cache_dir,
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


# Global configuration instance
_config: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """Get or create global configuration"""
    global _config
    if _config is None:
        _config = SystemConfig.from_environment()
        _config.create_directories()
    return _config


def load_config(env: Optional[str] = None) -> SystemConfig:
    """Load configuration for specific environment"""
    global _config
    _config = SystemConfig.from_environment(env)
    _config.create_directories()
    return _config
