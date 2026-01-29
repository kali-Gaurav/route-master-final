# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import settings
import os

Base = declarative_base()

_engine = None
_SessionLocal = None

def get_engine():
    """Get database engine with proper connection pooling"""
    global _engine
    if _engine is None:
        db_url = settings.database_url
        print(f"DEBUG db_connection: Creating engine with proper pooling")
        
        # SQLite doesn't support pooling
        if "sqlite" in db_url:
            _engine = create_engine(db_url, connect_args={"check_same_thread": False})
        else:
            # PostgreSQL with connection pooling
            _engine = create_engine(
                db_url,
                pool_size=20,                    # Number of connections to keep in pool
                max_overflow=0,                  # No overflow connections
                pool_pre_ping=True,              # Verify connections before use
                pool_recycle=3600,               # Recycle connections after 1 hour
                connect_args={"connect_timeout": 10}  # 10 second connection timeout
            )
        print(f"DEBUG db_connection: Engine created with pooling: {_engine}")
    else:
        print(f"DEBUG db_connection: Returning cached engine")
    return _engine

def get_sessionmaker():
    """Get sessionmaker, checking for test environment"""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        print(f"DEBUG db_connection: Creating sessionmaker bound to engine: {engine}")
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal

# Export engine as a lazy property - don't create it at module load time
# This ensures it uses the correct database URL (which may be overridden by tests)
@property
def engine():
    return get_engine()

# Use the existing database session
def get_db():
    """Dependency to get database session"""
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()