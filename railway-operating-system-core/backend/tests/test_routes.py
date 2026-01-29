# tests/test_routes.py
import pytest
from httpx import AsyncClient
from backend.models import User, Tenant, Route, Station, Train
from backend.core.security import get_password_hash
from uuid import uuid4

@pytest.mark.asyncio
class TestRouteAPI:
    """Test route management API endpoints"""

    async def test_get_routes_unauthorized(self, client):
        """Test getting routes without authentication"""
        response = await client.get("/v1/routes/")
        assert response.status_code == 401

    async def test_get_routes_authorized(self, client, db_session, test_user_data, test_tenant_data):
        """Test getting routes with authentication"""
        # Create tenant and user
        tenant = Tenant(**test_tenant_data)
        db_session.add(tenant)
        db_session.commit()

        hashed_password = get_password_hash(test_user_data["password"])
        user = User(
            tenant_id=tenant.id,
            email=test_user_data["email"],
            username=test_user_data["username"],
            first_name=test_user_data["first_name"],
            last_name=test_user_data["last_name"],
            hashed_password=hashed_password,
            role=test_user_data["role"]
        )
        db_session.add(user)
        db_session.commit()

        # Login to get token
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = await client.post("/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get routes (should return empty list initially)
        response = await client.get("/v1/routes/", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_search_routes(self, client, db_session, test_user_data, test_tenant_data):
        """Test route search functionality"""
        # Create tenant and user
        tenant = Tenant(**test_tenant_data)
        db_session.add(tenant)
        db_session.commit()

        hashed_password = get_password_hash(test_user_data["password"])
        user = User(
            tenant_id=tenant.id,
            email=test_user_data["email"],
            username=test_user_data["username"],
            first_name=test_user_data["first_name"],
            last_name=test_user_data["last_name"],
            hashed_password=hashed_password,
            role=test_user_data["role"]
        )
        db_session.add(user)
        db_session.commit()

        # Create test stations
        station1 = Station(
            name="Central Station",
            code="CS",
            city="Test City",
            country="Test Country"
        )
        station2 = Station(
            name="North Station",
            code="NS",
            city="Test City",
            country="Test Country"
        )
        db_session.add(station1)
        db_session.add(station2)
        db_session.commit()

        # Create test route
        route = Route(
            name="Test Route",
            origin_station_id=station1.id,
            destination_station_id=station2.id,
            distance=100.0,
            duration=120
        )
        db_session.add(route)
        db_session.commit()

        # Login to get token
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = await client.post("/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Search routes
        response = await client.get("/v1/routes/search", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_route_by_id(self, client, db_session, test_user_data, test_tenant_data):
        """Test getting specific route by ID"""
        # Create tenant, user, stations, and route
        tenant = Tenant(**test_tenant_data)
        db_session.add(tenant)
        db_session.commit()

        hashed_password = get_password_hash(test_user_data["password"])
        user = User(
            tenant_id=tenant.id,
            email=test_user_data["email"],
            username=test_user_data["username"],
            first_name=test_user_data["first_name"],
            last_name=test_user_data["last_name"],
            hashed_password=hashed_password,
            role=test_user_data["role"]
        )
        db_session.add(user)
        db_session.commit()

        station1 = Station(name="Central Station", code="CS", city="Test City", country="Test Country")
        station2 = Station(name="North Station", code="NS", city="Test City", country="Test Country")
        db_session.add(station1)
        db_session.add(station2)
        db_session.commit()

        route = Route(
            name="Test Route",
            origin_station_id=station1.id,
            destination_station_id=station2.id,
            distance=100.0,
            duration=120
        )
        db_session.add(route)
        db_session.commit()

        # Login to get token
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = await client.post("/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get route by ID
        response = await client.get(f"/v1/routes/{route.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Route"
        assert data["distance"] == 100.0

    async def test_get_nonexistent_route(self, client, db_session, test_user_data, test_tenant_data):
        """Test getting non-existent route"""
        # Create tenant and user
        tenant = Tenant(**test_tenant_data)
        db_session.add(tenant)
        db_session.commit()

        hashed_password = get_password_hash(test_user_data["password"])
        user = User(
            tenant_id=tenant.id,
            email=test_user_data["email"],
            username=test_user_data["username"],
            first_name=test_user_data["first_name"],
            last_name=test_user_data["last_name"],
            hashed_password=hashed_password,
            role=test_user_data["role"]
        )
        db_session.add(user)
        db_session.commit()

        # Login to get token
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = await client.post("/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to get non-existent route
        fake_id = str(uuid4())
        response = await client.get(f"/v1/routes/{fake_id}", headers=headers)
        assert response.status_code == 404
        assert "Route not found" in response.json()["detail"]