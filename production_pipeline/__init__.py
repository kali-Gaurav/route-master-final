"""
Production Pipeline Package

Railway Route Discovery Platform - Complete Production System

Modules:
- config: Configuration management (environment-based)
- database: SQLAlchemy ORM models and database management
- ingestion: Data fetching with async, rate limiting, caching
- data_pipeline: Validation, deduplication, normalization
- routing_engine: Route discovery using graph algorithms
- api: FastAPI REST API layer
- jobs: Background job scheduler
- observability: Logging, metrics, error tracking
- main: Application entry point

Usage:
    from production_pipeline.main import create_pipeline_app
    app, pipeline = create_pipeline_app()
    
or

    python -m production_pipeline.main
"""

__version__ = "1.0.0"
__author__ = "Route Master Team"
__description__ = "Production-grade railway route discovery platform"

from production_pipeline.config import get_config, get_python_executable_details
try:
    from database_manager import DatabaseManager
except ImportError:
    # Fallback if database module not available
    DatabaseManager = None
try:
    from production_pipeline.observability import initialize_observability
except ImportError:
    initialize_observability = None

__all__ = [
    "get_config",
    "DatabaseManager",
    "Base",
    "initialize_observability",
]
