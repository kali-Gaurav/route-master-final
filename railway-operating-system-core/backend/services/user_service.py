# services/user_service.py
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from ..models import User
from ..schemas.auth import UserCreate, UserUpdate
from ..core.security import get_password_hash, verify_password

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()

    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        return self.db.query(User).offset(skip).limit(limit).all()

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def create_user(self, user: UserCreate, is_active: bool = True) -> User:
        """Create new user"""
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            hashed_password=hashed_password,
            role=user.role,
            tenant_id=user.tenant_id,
            is_active=is_active
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def activate_user(self, user_id: UUID) -> bool:
        """Activate user account"""
        db_user = self.get_user(user_id)
        if not db_user:
            return False

        db_user.is_active = True
        self.db.commit()
        return True

    def update_user(self, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
        """Update existing user"""
        db_user = self.get_user(user_id)
        if not db_user:
            return None

        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "password":
                setattr(db_user, "hashed_password", get_password_hash(value))
            else:
                setattr(db_user, field, value)

        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def delete_user(self, user_id: UUID) -> bool:
        """Delete user"""
        db_user = self.get_user(user_id)
        if not db_user:
            return False

        self.db.delete(db_user)
        self.db.commit()
        return True

    def change_password(self, user_id: UUID, current_password: str, new_password: str) -> bool:
        """Change user password"""
        db_user = self.get_user(user_id)
        if not db_user:
            return False

        if not verify_password(current_password, db_user.hashed_password):
            return False

        db_user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        return True

    def set_password(self, user_id: UUID, new_password: str) -> bool:
        """Set new password for user (without current password verification)"""
        db_user = self.get_user(user_id)
        if not db_user:
            return False

        db_user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        return True