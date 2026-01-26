"""
Configuration Management System for Living Dataset Pipeline

Centralized configuration with environment variable support for:
- API endpoints and credentials
- Database connections
- Refresh intervals and thresholds
- File paths and storage settings
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
RAW_RAPPID_DIR = DATA_DIR / "raw_rappid"
STRUCTURED_DIR = DATA_DIR / "rappid_structured"
FETCH_LOGS_DIR = DATA_DIR / "fetch_logs"
ARCHIVES_DIR = DATA_DIR / "archives"
BACKUPS_DIR = DATA_DIR / "backups"

# Create directories if they don't exist
for directory in [DATA_DIR, LOGS_DIR, RAW_RAPPID_DIR, STRUCTURED_DIR, FETCH_LOGS_DIR, ARCHIVES_DIR, BACKUPS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # sqlite or postgresql
DB_SQLITE_PATH = DATA_DIR / "train_master.db"
DB_POSTGRESQL_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/train_master")

# RAPPID API Configuration
RAPPID_API_BASE = os.getenv("RAPPID_API_BASE", "https://rappid.zoppi.co.in")
RAPPID_API_TIMEOUT = int(os.getenv("RAPPID_API_TIMEOUT", "30"))
RAPPID_API_MAX_RETRIES = int(os.getenv("RAPPID_API_MAX_RETRIES", "3"))
RAPPID_API_BACKOFF_FACTOR = float(os.getenv("RAPPID_API_BACKOFF_FACTOR", "2.0"))

# IRCTC API Configuration
IRCTC_API_BASE = os.getenv("IRCTC_API_BASE", "https://api.railapi.com")
IRCTC_API_TIMEOUT = int(os.getenv("IRCTC_API_TIMEOUT", "30"))
IRCTC_API_KEY = os.getenv("IRCTC_API_KEY", "")

# Refresh Strategy Configuration
REFRESH_POLICY = {
    "new_train_fetch": True,  # Fetch new trains immediately
    "cache_valid_days": int(os.getenv("CACHE_VALID_DAYS", "7")),  # Use cache for < 7 days
    "refresh_after_days": int(os.getenv("REFRESH_AFTER_DAYS", "30")),  # Refresh after 30 days
    "unknown_train_check_days": int(os.getenv("UNKNOWN_TRAIN_CHECK_DAYS", "7")),  # Recheck unknown trains weekly
    "inactive_train_cleanup_days": int(os.getenv("INACTIVE_TRAIN_CLEANUP_DAYS", "90")),  # Mark dead after 90 days
}

# Rate Limiting Configuration
RATE_LIMIT = {
    "requests_per_second": float(os.getenv("RATE_LIMIT_RPS", "2.0")),
    "burst_limit": int(os.getenv("RATE_LIMIT_BURST", "10")),
    "circuit_breaker_threshold": int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5")),  # Fail after 5 errors
    "circuit_breaker_timeout": int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60")),  # Wait 60 seconds
}

# Caching Configuration
CACHE_CONFIG = {
    "max_size_mb": int(os.getenv("CACHE_MAX_SIZE_MB", "500")),
    "ttl_default_seconds": int(os.getenv("CACHE_TTL_SECONDS", "3600")),
    "ttl_per_train_seconds": int(os.getenv("CACHE_TTL_PER_TRAIN", "1800")),
    "compression_enabled": os.getenv("CACHE_COMPRESSION", "true").lower() == "true",
}

# Quality Scoring Configuration
QUALITY_SCORING = {
    "fresh_threshold_days": 7,  # < 7 days = 100%
    "acceptable_threshold_days": 14,  # 7-14 days = 80%
    "warning_threshold_days": 30,  # 14-30 days = 60%
    "critical_threshold_days": 90,  # > 30 days = 40%
}

# Alerting Configuration
ALERTS = {
    "inactive_train_percentage_threshold": float(os.getenv("ALERT_INACTIVE_THRESHOLD", "0.2")),  # 20%
    "api_failure_rate_threshold": float(os.getenv("ALERT_FAILURE_RATE_THRESHOLD", "0.1")),  # 10%
    "data_freshness_score_threshold": float(os.getenv("ALERT_FRESHNESS_THRESHOLD", "0.6")),  # 60%
    "enable_email_alerts": os.getenv("ENABLE_EMAIL_ALERTS", "false").lower() == "true",
    "alert_email_recipients": os.getenv("ALERT_EMAIL_RECIPIENTS", "").split(","),
    "enable_webhook_alerts": os.getenv("ENABLE_WEBHOOK_ALERTS", "false").lower() == "true",
    "webhook_url": os.getenv("WEBHOOK_URL", ""),
}

# Backup Configuration
BACKUP_CONFIG = {
    "enabled": os.getenv("BACKUP_ENABLED", "true").lower() == "true",
    "frequency_hours": int(os.getenv("BACKUP_FREQUENCY_HOURS", "24")),
    "retention_days": int(os.getenv("BACKUP_RETENTION_DAYS", "30")),
    "backup_location": BACKUPS_DIR,
    "compression_enabled": os.getenv("BACKUP_COMPRESSION", "true").lower() == "true",
}

# Scheduler Configuration
SCHEDULER_CONFIG = {
    "weekly_refresh_day": os.getenv("WEEKLY_REFRESH_DAY", "sunday"),
    "weekly_refresh_time": os.getenv("WEEKLY_REFRESH_TIME", "02:00"),
    "daily_validation_time": os.getenv("DAILY_VALIDATION_TIME", "12:00"),
    "health_check_interval_minutes": int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "log_dir": LOGS_DIR,
    "max_file_size_mb": int(os.getenv("LOG_MAX_SIZE_MB", "100")),
    "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "10")),
    "format": "json",  # json or standard
}

# Data Validation Configuration
VALIDATION_CONFIG = {
    "check_duplicates": True,
    "check_missing_fields": True,
    "check_invalid_dates": True,
    "check_platform_consistency": True,
    "check_station_sequence": True,
    "max_allowed_errors": int(os.getenv("MAX_VALIDATION_ERRORS", "100")),
}

# API Server Configuration
API_CONFIG = {
    "host": os.getenv("API_HOST", "0.0.0.0"),
    "port": int(os.getenv("API_PORT", "5000")),
    "debug": os.getenv("API_DEBUG", "false").lower() == "true",
    "cors_enabled": os.getenv("CORS_ENABLED", "true").lower() == "true",
}

# Data Retention Configuration
DATA_RETENTION = {
    "keep_raw_data_days": int(os.getenv("KEEP_RAW_DATA_DAYS", "365")),
    "keep_structured_data_days": int(os.getenv("KEEP_STRUCTURED_DATA_DAYS", "180")),
    "keep_logs_days": int(os.getenv("KEEP_LOGS_DAYS", "90")),
    "archive_old_data": os.getenv("ARCHIVE_OLD_DATA", "true").lower() == "true",
}

# System Configuration
SYSTEM_CONFIG = {
    "max_concurrent_api_requests": int(os.getenv("MAX_CONCURRENT_REQUESTS", "10")),
    "timeout_seconds": int(os.getenv("SYSTEM_TIMEOUT", "300")),
    "memory_limit_mb": int(os.getenv("MEMORY_LIMIT_MB", "2048")),
    "enable_metrics": os.getenv("ENABLE_METRICS", "true").lower() == "true",
}


class ConfigValidator:
    """Validate configuration on startup"""
    
    @staticmethod
    def validate() -> tuple[bool, list[str]]:
        """
        Validate all configuration settings
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate database configuration
        if DB_TYPE not in ["sqlite", "postgresql"]:
            errors.append(f"Invalid DB_TYPE: {DB_TYPE}")
        
        if DB_TYPE == "sqlite" and not DB_SQLITE_PATH.parent.exists():
            errors.append(f"SQLite directory does not exist: {DB_SQLITE_PATH.parent}")
        
        # Validate refresh policy values
        if REFRESH_POLICY["cache_valid_days"] >= REFRESH_POLICY["refresh_after_days"]:
            errors.append("cache_valid_days must be less than refresh_after_days")
        
        # Validate rate limiting
        if RATE_LIMIT["requests_per_second"] <= 0:
            errors.append("requests_per_second must be positive")
        
        # Validate directories
        for directory in [DATA_DIR, LOGS_DIR, RAW_RAPPID_DIR, STRUCTURED_DIR]:
            if not directory.exists():
                errors.append(f"Directory does not exist: {directory}")
        
        return len(errors) == 0, errors


# Validate configuration on import
is_valid, validation_errors = ConfigValidator.validate()
if not is_valid:
    print("⚠️  Configuration validation errors:")
    for error in validation_errors:
        print(f"  - {error}")
