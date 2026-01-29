# tests/test_auth.py
import pytest
from httpx import AsyncClient
from backend.models import User, Tenant
from backend.core.security import get_password_hash

@pytest.mark.asyncio
class TestAuthenticationAPI:
    """Test authentication API endpoints"""

    async def test_user_registration(self, client, db_session, test_user_data, test_tenant_data):
        """Test user registration endpoint"""
        # Create tenant first
        tenant = Tenant(**test_tenant_data)
        db_session.add(tenant)
        db_session.commit()

        user_data = test_user_data.copy()
        user_data["tenant_id"] = str(tenant.id)

        response = await client.post("/v1/auth/register", json=user_data)
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["role"] == user_data["role"]
        assert "id" in data

    async def test_user_login(self, client, db_session, test_user_data, test_tenant_data):
        """Test user login endpoint"""
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

        # Test login
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }

        response = await client.post("/v1/auth/login", data=login_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_invalid_login(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }

        response = await client.post("/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    async def test_get_current_user(self, client, db_session, test_user_data, test_tenant_data):
        """Test getting current user info"""
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

        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/v1/auth/me", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["role"] == test_user_data["role"]

    async def test_unauthorized_access(self, client):
        """Test accessing protected endpoint without token"""
        response = await client.get("/v1/auth/me")
        assert response.status_code == 401

    async def test_token_refresh(self, client, db_session, test_user_data, test_tenant_data):
        """Test token refresh endpoint"""
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

        # Refresh token
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post("/v1/auth/refresh", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify new token works
        new_token = data["access_token"]
        headers = {"Authorization": f"Bearer {new_token}"}
        response = await client.get("/v1/auth/me", headers=headers)
        assert response.status_code == 200

@pytest.mark.asyncio
class TestAuthorization:
    """Test role-based authorization"""

    async def test_role_hierarchy(self, client, db_session):
        """Test role hierarchy permissions"""
        # Create tenant
        tenant = Tenant(name="Test Tenant", domain="test.com")
        db_session.add(tenant)
        db_session.commit()

        # Create users with different roles
        roles = ["guest", "user", "operator", "developer", "admin"]
        users = {}
        test_password = "TestPass123!"  # Meets complexity requirements

        for role in roles:
            hashed_password = get_password_hash(test_password)
            user = User(
                tenant_id=tenant.id,
                email=f"{role}@example.com",
                username=role,
                first_name=role.title(),
                last_name="User",
                hashed_password=hashed_password,
                role=role
            )
            db_session.add(user)
            users[role] = user

        db_session.commit()

        # Test that all roles can login
        for role, user in users.items():
            login_data = {
                "username": user.email,
                "password": test_password
            }
            response = await client.post("/v1/auth/login", data=login_data)
            assert response.status_code == 200