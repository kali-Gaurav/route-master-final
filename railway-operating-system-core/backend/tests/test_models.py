# tests/test_models.py
import pytest
from backend.models import User, Tenant
from uuid import uuid4

class TestUserModel:
    """Test User model functionality"""

    def test_user_creation(self, db_session):
        """Test creating a user"""
        tenant = Tenant(name="Test Tenant", domain="test.com")
        db_session.add(tenant)
        db_session.commit()

        user = User(
            tenant_id=tenant.id,
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            hashed_password="hashedpassword",
            role="user"
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.role == "user"
        assert user.is_active == True

    def test_user_relationships(self, db_session):
        """Test user-tenant relationships"""
        tenant = Tenant(name="Test Tenant", domain="test.com")
        db_session.add(tenant)
        db_session.commit()

        user = User(
            tenant_id=tenant.id,
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            hashed_password="hashedpassword",
            role="user"
        )
        db_session.add(user)
        db_session.commit()

        # Test relationship
        assert user.tenant == tenant
        assert user in tenant.users

    def test_user_unique_constraints(self, db_session):
        """Test unique constraints on email and username"""
        tenant = Tenant(name="Test Tenant", domain="test.com")
        db_session.add(tenant)
        db_session.commit()

        user1 = User(
            tenant_id=tenant.id,
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            hashed_password="hashedpassword",
            role="user"
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create duplicate email
        user2 = User(
            tenant_id=tenant.id,
            email="test@example.com",  # duplicate
            username="testuser2",
            first_name="Test2",
            last_name="User2",
            hashed_password="hashedpassword",
            role="user"
        )
        db_session.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

class TestTenantModel:
    """Test Tenant model functionality"""

    def test_tenant_creation(self, db_session):
        """Test creating a tenant"""
        tenant = Tenant(name="Test Tenant", domain="test.com")
        db_session.add(tenant)
        db_session.commit()

        assert tenant.id is not None
        assert tenant.name == "Test Tenant"
        assert tenant.domain == "test.com"
        assert tenant.is_active == True

    def test_tenant_unique_constraints(self, db_session):
        """Test unique constraints on name and domain"""
        tenant1 = Tenant(name="Test Tenant", domain="test.com")
        db_session.add(tenant1)
        db_session.commit()

        # Try duplicate name
        tenant2 = Tenant(name="Test Tenant", domain="test2.com")
        db_session.add(tenant2)
        with pytest.raises(Exception):
            db_session.commit()