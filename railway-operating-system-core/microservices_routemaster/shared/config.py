# ===============================================
# SHARED CONFIGURATION
# ===============================================
# Configuration constants and utilities for microservices

import os
from typing import Dict, Any
from datetime import timedelta

# ===============================================
# SERVICE PORTS AND URLs
# ===============================================

SERVICE_PORTS = {
    'api_gateway': int(os.getenv('API_GATEWAY_PORT', '8000')),
    'auth_service': int(os.getenv('AUTH_SERVICE_PORT', '8001')),
    'route_service': int(os.getenv('ROUTE_SERVICE_PORT', '8002')),
    'data_service': int(os.getenv('DATA_SERVICE_PORT', '8003')),
    'worker_service': int(os.getenv('WORKER_SERVICE_PORT', '8004')),
}

SERVICE_URLS = {
    'api_gateway': os.getenv('API_GATEWAY_URL', 'http://localhost:8000'),
    'auth_service': os.getenv('AUTH_SERVICE_URL', 'http://localhost:8001'),
    'route_service': os.getenv('ROUTE_SERVICE_URL', 'http://localhost:8002'),
    'data_service': os.getenv('DATA_SERVICE_URL', 'http://localhost:8003'),
    'worker_service': os.getenv('WORKER_SERVICE_URL', 'http://localhost:8004'),
}

# ===============================================
# DATABASE CONFIGURATION
# ===============================================

DATABASE_CONFIG = {
    'url': os.getenv('DATABASE_URL', 'postgresql://railway_user:railway_password@localhost:5432/railway_os'),
    'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
    'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')),
    'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
    'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),
}

# ===============================================
# REDIS CONFIGURATION
# ===============================================

REDIS_CONFIG = {
    'url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
    'db': int(os.getenv('REDIS_DB', '0')),
    'ttl': int(os.getenv('REDIS_TTL', '3600')),  # 1 hour default TTL
}

# ===============================================
# RABBITMQ CONFIGURATION
# ===============================================

RABBITMQ_CONFIG = {
    'url': os.getenv('RABBITMQ_URL', 'amqp://railway_user:railway_password@localhost:5672/'),
    'exchange': os.getenv('RABBITMQ_EXCHANGE', 'railway_os'),
    'queue': os.getenv('RABBITMQ_QUEUE', 'route_jobs'),
}

# ===============================================
# ROUTE SEARCH CONFIGURATION
# ===============================================

ROUTE_CONFIG = {
    'max_transfers': int(os.getenv('MAX_TRANSFERS', '3')),
    'default_page_size': int(os.getenv('DEFAULT_PAGE_SIZE', '10')),
    'max_route_results': int(os.getenv('MAX_ROUTE_RESULTS', '100')),
    'cache_ttl': int(os.getenv('ROUTE_CACHE_TTL', '3600')),  # 1 hour
    'min_transfer_time': int(os.getenv('MIN_TRANSFER_TIME', '30')),  # minutes
}

# ===============================================
# API CONFIGURATION
# ===============================================

API_CONFIG = {
    'version': 'v1',
    'title': 'Railway Operating System API',
    'description': 'Production-grade route finding and scheduling API',
    'debug_mode': os.getenv('DEBUG_MODE', 'false').lower() == 'true',
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
}

# ===============================================
# AUTHENTICATION & SECURITY
# ===============================================

AUTH_CONFIG = {
    'api_key_header': 'Authorization',
    'api_key_prefix': 'Bearer ',
    'default_rate_limit_per_minute': int(os.getenv('DEFAULT_RATE_LIMIT_MINUTE', '1000')),
    'default_rate_limit_per_hour': int(os.getenv('DEFAULT_RATE_LIMIT_HOUR', '10000')),
    'token_expiry_days': int(os.getenv('TOKEN_EXPIRY_DAYS', '365')),
}

# ===============================================
# JOB PROCESSING CONFIGURATION
# ===============================================

JOB_CONFIG = {
    'max_retries': int(os.getenv('JOB_MAX_RETRIES', '3')),
    'retry_delay': int(os.getenv('JOB_RETRY_DELAY', '60')),  # seconds
    'timeout': int(os.getenv('JOB_TIMEOUT', '300')),  # 5 minutes
    'concurrency': int(os.getenv('JOB_CONCURRENCY', '4')),
}

# ===============================================
# MONITORING & LOGGING
# ===============================================

MONITORING_CONFIG = {
    'metrics_enabled': os.getenv('METRICS_ENABLED', 'true').lower() == 'true',
    'health_check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', '30')),
    'log_format': os.getenv('LOG_FORMAT', 'json'),
    'enable_audit_log': os.getenv('ENABLE_AUDIT_LOG', 'true').lower() == 'true',
}

# ===============================================
# TRAIN TYPES AND FARE CLASSES
# ===============================================

TRAIN_TYPES = ['GENERAL', 'PASSENGER', 'EXPRESS', 'MEMU', 'DEMU', 'OTHERS']

FARE_CLASSES = {
    '1A': '1st AC',
    '2A': '2nd AC',
    '3A': '3rd AC',
    'SL': 'Sleeper',
    'CC': 'Chair Car',
    '2S': '2nd Seating'
}

DAYS_OF_WEEK = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

# ===============================================
# MAJOR STATIONS (can be extended per tenant)
# ===============================================

MAJOR_STATIONS = {
    'NDLS': 'New Delhi',
    'BCT': 'Mumbai Central',
    'HWH': 'Howrah Junction',
    'MAS': 'Chennai Central',
    'SBC': 'Bangalore City',
    'PUNE': 'Pune Junction',
    'LKO': 'Lucknow',
    'KOL': 'Kolkata',
    'AMD': 'Ahmedabad',
    'HYB': 'Hyderabad'
}

# ===============================================
# UTILITY FUNCTIONS
# ===============================================

def get_service_url(service_name: str) -> str:
    """Get URL for a service"""
    return SERVICE_URLS.get(service_name, f'http://localhost:{SERVICE_PORTS.get(service_name, 8000)}')

def get_env_var(name: str, default: Any = None) -> Any:
    """Get environment variable with type conversion"""
    value = os.getenv(name)
    if value is None:
        return default

    # Type conversion based on default value type
    if default is not None:
        if isinstance(default, bool):
            return value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(default, int):
            try:
                return int(value)
            except ValueError:
                return default
        elif isinstance(default, float):
            try:
                return float(value)
            except ValueError:
                return default

    return value

def is_production() -> bool:
    """Check if running in production environment"""
    return os.getenv('ENVIRONMENT', 'development').lower() == 'production'

def get_cors_origins() -> list:
    """Get allowed CORS origins"""
    origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8080')
    return [origin.strip() for origin in origins.split(',') if origin.strip()]