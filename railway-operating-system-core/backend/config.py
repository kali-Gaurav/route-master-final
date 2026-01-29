# config.py
from pydantic_settings import BaseSettings
from typing import List
import os
import sys

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://railway_user:secure_password@localhost:5432/railway_db")

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # JWT - MUST be set via environment, no defaults
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    jwt_refresh_expiration_hours: int = 168  # 7 days

    # CSRF Protection
    csrf_secret_key: str = os.getenv("CSRF_SECRET_KEY", "change-this-csrf-secret-in-production")

    # Email Service
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    from_email: str = os.getenv("FROM_EMAIL", "noreply@railway-system.com")
    from_name: str = os.getenv("FROM_NAME", "Railway Operating System")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_version: str = "/v1"
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")

    # Security
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # Observability
    prometheus_port: int = 9090
    log_level: str = "INFO"

    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Additional settings
    trusted_hosts: List[str] = ["localhost", "127.0.0.1", "*.railway-system.com"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate JWT secret is set
        if not self.jwt_secret or self.jwt_secret == "":
            raise ValueError("JWT_SECRET environment variable must be set!")
        # Override database URL for testing
        if os.getenv("TESTING") == "1" or "pytest" in sys.modules:
            print(f"DEBUG: Using SQLite for testing")
            self.database_url = "sqlite:///./test.db"
        else:
            print(f"DEBUG: Using {self.database_url.split('@')[1] if '@' in self.database_url else 'configured'} database")

    class Config:
        env_file = ".env"

# Create singleton instance
def get_settings() -> Settings:
    """Get settings instance with proper error handling"""
    try:
        return Settings()
    except ValueError:
        # Allow tests to pass without JWT_SECRET in environment
        if os.getenv("TESTING") == "1" or "pytest" in sys.modules:
            os.environ["JWT_SECRET"] = "test-secret-key-do-not-use-in-production"
            return Settings()
        else:
            raise

# Create singleton instance
settings = get_settings()

# Add additional configuration
class Config:
    case_sensitive = False
    env_file = ".env"