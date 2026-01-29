# tests/test_services.py
import pytest
from backend.services.user_service import UserService
from backend.services.route_service import RouteService
from backend.models import User, Tenant, Route, Station
from backend.core.security import get_password_hash
from backend.schemas.auth import UserCreate, UserUpdate
from uuid import uuid4

class TestUserService:
    """Test UserService functionality"""

    def test_create_user(self, db_session, test_tenant_data):
        """Test creating a user"""
        # Create tenant
        tenant = Tenant(**test_tenant_data)
        db_session.add(tenant)
        db_session.commit()

        user_service = UserService(db_session)

        user_data = UserCreate(
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )

        user = user_service.create_user(user_data)

        assert user.email == "test@example.com"
        assert user.tenant_id == tenant.id
        assert user.is_active == True
        assert user.role == "user"  # default role

    def test_authenticate_user(self, db_session, test_tenant_data):
        """Test user authentication"""
        # Create tenant
        tenant = Tenant(**test_tenant_data)
        db_session.add(tenant)
        db_session.commit()

        user_service = UserService(db_session)

        # Create user
        user_data = UserCreate(
            email="auth@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        user_service.create_user(user_data)

        # Test authentication
        authenticated_user = user_service.authenticate_user("auth@example.com", "password123")
        assert authenticated_user is not None
        assert authenticated_user.email == "auth@example.com"

        # Test wrong password
        wrong_auth = user_service.authenticate_user("auth@example.com", "wrongpassword")
        assert wrong_auth is None

        # Test non-existent user
        nonexistent_auth = user_service.authenticate_user("nonexistent@example.com", "password123")
        assert nonexistent_auth is None

    def test_get_user_by_email(self, db_session, test_tenant_data):
        """Test getting user by email"""
        # Create tenant
        tenant = Tenant(**test_tenant_data)
        db_session.add(tenant)
        db_session.commit()

        user_service = UserService(db_session)

        # Create user
        user_data = UserCreate(
            email="get@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        created_user = user_service.create_user(user_data)

        # Get user by email
        retrieved_user = user_service.get_user_by_email("get@example.com")
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id

        # Test non-existent email
        nonexistent_user = user_service.get_user_by_email("nonexistent@example.com")
        assert nonexistent_user is None

    def test_update_user(self, db_session, test_tenant_data):
        """Test updating user information"""
        # Create tenant
        tenant = Tenant(**test_tenant_data)
        db_session.add(tenant)
        db_session.commit()

        user_service = UserService(db_session)

        # Create user
        user_data = UserCreate(
            email="update@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        created_user = user_service.create_user(user_data)

        # Update user
        update_data = UserUpdate(
            first_name="Updated",
            last_name="Name",
            role="operator"
        )
        updated_user = user_service.update_user(created_user.id, update_data)

        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        assert updated_user.role == "operator"

class TestRouteService:
    """Test RouteService functionality"""

    def test_search_routes_empty(self, db_session):
        """Test searching routes with no data"""
        route_service = RouteService(db_session)

        from backend.schemas.route import RouteSearch
        search = RouteSearch()

        results = route_service.search_routes(search)
        assert results == []

    def test_search_routes_with_data(self, db_session):
        """Test searching routes with data"""
        # Create stations
        station1 = Station(
            name="Station A",
            code="STA",
            city="City A",
            country="Country A"
        )
        station2 = Station(
            name="Station B",
            code="STB",
            city="City B",
            country="Country B"
        )
        db_session.add(station1)
        db_session.add(station2)
        db_session.commit()

        # Create route
        route = Route(
            name="Test Route",
            origin_station_id=station1.id,
            destination_station_id=station2.id,
            distance=150.0,
            duration=180
        )
        db_session.add(route)
        db_session.commit()

        route_service = RouteService(db_session)

        from backend.schemas.route import RouteSearch
        search = RouteSearch()

        results = route_service.search_routes(search)
        assert len(results) == 1
        assert results[0].name == "Test Route"

    def test_get_route(self, db_session):
        """Test getting a specific route"""
        # Create stations and route
        station1 = Station(name="Station A", code="STA", city="City A", country="Country A")
        station2 = Station(name="Station B", code="STB", city="City B", country="Country B")
        db_session.add(station1)
        db_session.add(station2)
        db_session.commit()

        route = Route(
            name="Test Route",
            origin_station_id=station1.id,
            destination_station_id=station2.id,
            distance=150.0,
            duration=180
        )
        db_session.add(route)
        db_session.commit()

        route_service = RouteService(db_session)

        retrieved_route = route_service.get_route(route.id)
        assert retrieved_route is not None
        assert retrieved_route.name == "Test Route"

        # Test non-existent route
        fake_id = str(uuid4())
        nonexistent_route = route_service.get_route(fake_id)
        assert nonexistent_route is None