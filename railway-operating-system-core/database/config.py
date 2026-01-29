# config.py - Comprehensive Configuration Management
import os
from typing import Optional
from dataclasses import dataclass
from datetime import timedelta

@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    
    # Connection Settings
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    database: str = os.getenv('DB_NAME', 'railway_os')
    username: str = os.getenv('DB_USER', 'postgres')
    password: str = os.getenv('DB_PASSWORD', 'password')
    
    # Connection Pool Settings
    pool_size: int = int(os.getenv('DB_POOL_SIZE', '20'))
    max_overflow: int = int(os.getenv('DB_MAX_OVERFLOW', '30'))
    pool_timeout: int = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    pool_recycle: int = int(os.getenv('DB_POOL_RECYCLE', '3600'))
    pool_pre_ping: bool = os.getenv('DB_POOL_PRE_PING', 'true').lower() == 'true'
    
    # Query Logging and Monitoring
    enable_query_logging: bool = os.getenv('DB_ENABLE_QUERY_LOGGING', 'false').lower() == 'true'
    enable_performance_monitoring: bool = os.getenv('DB_ENABLE_PERF_MONITORING', 'true').lower() == 'true'
    slow_query_threshold: float = float(os.getenv('DB_SLOW_QUERY_THRESHOLD', '1.0'))
    
    # Health Check Settings
    health_check_interval: int = int(os.getenv('DB_HEALTH_CHECK_INTERVAL', '60'))
    max_retries: int = int(os.getenv('DB_MAX_RETRIES', '3'))
    retry_delay: float = float(os.getenv('DB_RETRY_DELAY', '0.5'))
    retry_backoff: float = float(os.getenv('DB_RETRY_BACKOFF', '2.0'))
    
    # Read Replica Settings (Optional)
    read_replica_url: str = os.getenv('DB_READ_REPLICA_URL', '')
    enable_read_replica: bool = bool(read_replica_url)
    
    # Multi-Tenancy Settings
    tenancy_model: str = os.getenv('DB_TENANCY_MODEL', 'schema')  # 'schema' or 'database'
    enable_row_level_security: bool = os.getenv('DB_ENABLE_RLS', 'true').lower() == 'true'
    
    @property
    def connection_string(self) -> str:
        """Build PostgreSQL connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class BackupConfig:
    """Backup and recovery configuration."""
    
    # Backup Strategy
    backup_type: str = os.getenv('BACKUP_TYPE', 'full')  # full, incremental
    backup_format: str = os.getenv('BACKUP_FORMAT', 'tar')  # tar, directory
    enable_compression: bool = os.getenv('BACKUP_COMPRESSION', 'true').lower() == 'true'
    compression_level: int = int(os.getenv('BACKUP_COMPRESSION_LEVEL', '6'))
    
    # Backup Schedule
    backup_schedule_time: str = os.getenv('BACKUP_SCHEDULE_TIME', '02:00')  # HH:MM format
    backup_schedule_interval: str = os.getenv('BACKUP_SCHEDULE_INTERVAL', 'daily')  # daily, weekly, monthly
    enable_incremental_backups: bool = os.getenv('BACKUP_INCREMENTAL', 'true').lower() == 'true'
    
    # Retention Policy
    retention_full_backups: int = int(os.getenv('BACKUP_RETENTION_FULL_DAYS', '30'))
    retention_incremental_backups: int = int(os.getenv('BACKUP_RETENTION_INCREMENTAL_DAYS', '7'))
    retention_transaction_logs: int = int(os.getenv('BACKUP_RETENTION_LOGS_DAYS', '14'))
    
    # S3 Configuration
    s3_enabled: bool = os.getenv('S3_ENABLED', 'true').lower() == 'true'
    s3_bucket: str = os.getenv('S3_BUCKET', 'railway-db-backups')
    s3_region: str = os.getenv('S3_REGION', 'us-east-1')
    s3_prefix: str = os.getenv('S3_PREFIX', 'backups/railway-os/')
    aws_access_key_id: str = os.getenv('AWS_ACCESS_KEY_ID', '')
    aws_secret_access_key: str = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    
    # Local Backup Settings
    local_backup_enabled: bool = os.getenv('LOCAL_BACKUP_ENABLED', 'true').lower() == 'true'
    local_backup_path: str = os.getenv('LOCAL_BACKUP_PATH', '/var/lib/postgresql/backups')
    local_retention_days: int = int(os.getenv('LOCAL_BACKUP_RETENTION_DAYS', '30'))
    
    # PITR (Point-in-Time Recovery) Settings
    enable_pitr: bool = os.getenv('PITR_ENABLED', 'true').lower() == 'true'
    wal_level: str = 'replica'  # Must be 'replica' for PITR
    archive_mode: bool = True
    archive_command: str = os.getenv('WAL_ARCHIVE_COMMAND', 'cp %p /var/lib/postgresql/archive/%f')
    archive_timeout: int = int(os.getenv('WAL_ARCHIVE_TIMEOUT', '300'))
    
    # Backup Verification
    enable_backup_verification: bool = os.getenv('BACKUP_VERIFY', 'true').lower() == 'true'
    verify_method: str = os.getenv('BACKUP_VERIFY_METHOD', 'checksums')  # checksums, restore


@dataclass
class MonitoringConfig:
    """System monitoring configuration."""
    
    # Health Check
    enable_health_checks: bool = os.getenv('MONITORING_ENABLED', 'true').lower() == 'true'
    health_check_interval_seconds: int = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))
    
    # Performance Monitoring
    enable_query_performance_monitoring: bool = os.getenv('QUERY_PERF_MONITORING', 'true').lower() == 'true'
    slow_query_log_enabled: bool = os.getenv('SLOW_QUERY_LOG', 'true').lower() == 'true'
    slow_query_threshold_ms: float = float(os.getenv('SLOW_QUERY_THRESHOLD_MS', '1000'))
    
    # Schema Monitoring
    enable_schema_drift_detection: bool = os.getenv('SCHEMA_DRIFT_DETECTION', 'true').lower() == 'true'
    schema_check_interval_hours: int = int(os.getenv('SCHEMA_CHECK_INTERVAL_HOURS', '24'))
    
    # Metrics Collection
    enable_metrics_collection: bool = os.getenv('METRICS_COLLECTION', 'true').lower() == 'true'
    metrics_retention_days: int = int(os.getenv('METRICS_RETENTION_DAYS', '30'))
    
    # Alerting
    enable_alerts: bool = os.getenv('ALERTS_ENABLED', 'true').lower() == 'true'
    alert_email: str = os.getenv('ALERT_EMAIL', '')
    alert_threshold_cpu: float = float(os.getenv('ALERT_CPU_THRESHOLD', '80.0'))
    alert_threshold_memory: float = float(os.getenv('ALERT_MEMORY_THRESHOLD', '85.0'))
    alert_threshold_disk: float = float(os.getenv('ALERT_DISK_THRESHOLD', '90.0'))


@dataclass
class SecurityConfig:
    """Security configuration."""
    
    # JWT Settings
    jwt_enabled: bool = os.getenv('JWT_ENABLED', 'true').lower() == 'true'
    jwt_secret: str = os.getenv('JWT_SECRET', 'your-super-secret-key-change-this')
    jwt_algorithm: str = os.getenv('JWT_ALGORITHM', 'HS256')
    jwt_expiration_minutes: int = int(os.getenv('JWT_EXPIRATION_MINUTES', '60'))
    
    # Row-Level Security
    enable_rls: bool = os.getenv('ENABLE_RLS', 'true').lower() == 'true'
    
    # API Key Settings
    api_key_expiration_days: int = int(os.getenv('API_KEY_EXPIRATION_DAYS', '90'))
    enable_api_key_rotation: bool = os.getenv('API_KEY_ROTATION', 'true').lower() == 'true'
    
    # Encryption
    enable_encryption_at_rest: bool = os.getenv('ENCRYPTION_AT_REST', 'true').lower() == 'true'
    encryption_algorithm: str = os.getenv('ENCRYPTION_ALGORITHM', 'AES-256')
    
    # Audit Logging
    enable_audit_logging: bool = os.getenv('AUDIT_LOGGING', 'true').lower() == 'true'
    audit_log_retention_days: int = int(os.getenv('AUDIT_LOG_RETENTION_DAYS', '90'))


@dataclass
class ApplicationConfig:
    """Application configuration."""
    
    # Environment
    environment: str = os.getenv('ENVIRONMENT', 'development')  # development, staging, production
    debug_mode: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # API Settings
    api_host: str = os.getenv('API_HOST', '0.0.0.0')
    api_port: int = int(os.getenv('API_PORT', '8000'))
    api_version: str = os.getenv('API_VERSION', 'v1')
    
    # Job Queue Settings
    enable_job_queue: bool = os.getenv('JOB_QUEUE_ENABLED', 'true').lower() == 'true'
    max_concurrent_jobs: int = int(os.getenv('MAX_CONCURRENT_JOBS', '10'))
    job_timeout_minutes: int = int(os.getenv('JOB_TIMEOUT_MINUTES', '60'))
    
    # Data Validation
    enable_strict_validation: bool = os.getenv('STRICT_VALIDATION', 'true').lower() == 'true'
    
    # Logging
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_format: str = os.getenv('LOG_FORMAT', 'json')  # json, text


class Config:
    """Main configuration class that brings all configs together."""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.backup = BackupConfig()
        self.monitoring = MonitoringConfig()
        self.security = SecurityConfig()
        self.application = ApplicationConfig()
    
    def validate(self) -> list:
        """Validate all configuration settings."""
        issues = []
        
        # Database validation
        if not self.database.host:
            issues.append("Database host is required")
        if self.database.port <= 0 or self.database.port > 65535:
            issues.append("Invalid database port")
        if not self.database.database:
            issues.append("Database name is required")
        
        # Backup validation
        if self.backup.s3_enabled and not self.backup.s3_bucket:
            issues.append("S3 bucket is required when S3 backups are enabled")
        if self.backup.local_backup_enabled and not self.backup.local_backup_path:
            issues.append("Local backup path is required when local backups are enabled")
        
        # Security validation
        if self.security.jwt_enabled and self.security.jwt_secret == 'your-super-secret-key-change-this':
            issues.append("JWT secret must be changed from default value")
        
        return issues
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.application.environment == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.application.environment == 'development'
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            'environment': self.application.environment,
            'debug': self.application.debug_mode,
            'database': {
                'host': self.database.host,
                'port': self.database.port,
                'database': self.database.database,
                'pool_size': self.database.pool_size,
            },
            'backup': {
                's3_enabled': self.backup.s3_enabled,
                'local_enabled': self.backup.local_backup_enabled,
                'pitr_enabled': self.backup.enable_pitr,
            },
            'monitoring': {
                'enabled': self.monitoring.enable_health_checks,
                'check_interval_seconds': self.monitoring.health_check_interval_seconds,
            },
            'security': {
                'rls_enabled': self.security.enable_rls,
                'audit_logging': self.security.enable_audit_logging,
            },
        }


# Global configuration instance
config = Config()
