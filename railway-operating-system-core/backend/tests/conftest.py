# tests/conftest.py
import pytest
import os

# Set TESTING environment variable at module level BEFORE any imports
os.environ["TESTING"] = "1"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import User, Tenant  # Import models to ensure they're registered
from backend.db_connection import Base, get_db
from backend.config import settings
import backend.db_connection as db_connection

# Reset the global engine and sessionmaker caches to use test database
db_connection._engine = None
db_connection._SessionLocal = None

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    # Create engine with test SQLite database
    engine = create_engine("sqlite:///./test.db", echo=False)
    print(f"DEBUG conftest: test_engine created: {engine}")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create test database session"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    print(f"DEBUG conftest: db_session created with engine: {test_engine}")
    
    # Clear all tables before each test to ensure isolation
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def client(db_session):
    """Test client for FastAPI app"""
    from backend.main import app
    from httpx import AsyncClient
    from db_connection import get_db
    import db_connection
    
    # Override the global cached sessionmaker to ensure test database is used
    db_connection._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_session.get_bind())
    
    # Override the get_db dependency to use the test session
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    return AsyncClient(app=app, base_url="http://testserver")

@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "password": "TestPass123!",  # Meets complexity: uppercase, lowercase, digit, special char (12 chars, under 72 byte limit)
        "role": "user"
    }

@pytest.fixture
def test_tenant_data():
    """Sample tenant data for testing"""
    return {
        "name": "Test Tenant",
        "domain": "test.example.com"
    }