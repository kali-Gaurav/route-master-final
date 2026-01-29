# services/encryption_manager.py - Data Encryption and Protection
"""
Encryption utilities for protecting sensitive data at rest.
Supports field-level encryption, key management, and data masking.
"""

import sys
from pathlib import Path
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EncryptionManager:
    """Manage data encryption for sensitive fields."""

    def __init__(self, master_key: str = None):
        """Initialize encryption manager with master key."""
        if master_key is None:
            master_key = os.getenv('ENCRYPTION_MASTER_KEY', 'default-master-key')
        
        self.master_key = master_key
        self.cipher = self._create_cipher(master_key)

    def _create_cipher(self, key: str) -> Fernet:
        """Create Fernet cipher from master key."""
        try:
            # Derive key from master key
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'railway_os_salt_',  # In production, use random salt
                iterations=100000,
                backend=default_backend()
            )
            
            derived_key = kdf.derive(key.encode())
            encoded_key = base64.urlsafe_b64encode(derived_key)
            
            return Fernet(encoded_key)

        except Exception as e:
            logger.error(f"Failed to create cipher: {e}")
            return None

    def encrypt_field(self, plaintext: str) -> str:
        """Encrypt a sensitive field."""
        try:
            if not plaintext:
                return None
            
            encrypted = self.cipher.encrypt(plaintext.encode())
            return encrypted.decode()

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None

    def decrypt_field(self, ciphertext: str) -> str:
        """Decrypt an encrypted field."""
        try:
            if not ciphertext:
                return None
            
            decrypted = self.cipher.decrypt(ciphertext.encode())
            return decrypted.decode()

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt (one-way)."""
        try:
            import bcrypt
            
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(password.encode(), salt)
            return hashed.decode()

        except ImportError:
            logger.warning("bcrypt not installed, using basic hashing")
            # Fallback: use Fernet encryption
            return self.encrypt_field(password)

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            import bcrypt
            return bcrypt.checkpw(password.encode(), hashed.encode())

        except ImportError:
            # Fallback: compare Fernet encryption
            return self.decrypt_field(hashed) == password

    def mask_sensitive_data(self, data: str, mask_type: str = 'email') -> str:
        """Mask sensitive data for display/logging."""
        if not data:
            return None
        
        if mask_type == 'email':
            # mask.user@domain.com
            parts = data.split('@')
            if len(parts) == 2:
                user, domain = parts
                masked_user = user[0] + '*' * (len(user) - 2) + user[-1]
                return f"{masked_user}@{domain}"
        
        elif mask_type == 'phone':
            # ***-****-0123
            return '*' * (len(data) - 4) + data[-4:]
        
        elif mask_type == 'card':
            # ****-****-****-0123
            return '*' * (len(data) - 4) + data[-4:]
        
        elif mask_type == 'generic':
            # Show first and last character only
            if len(data) <= 2:
                return '*' * len(data)
            return data[0] + '*' * (len(data) - 2) + data[-1]
        
        return data

    def create_encryption_key(self) -> str:
        """Generate a new encryption key."""
        return Fernet.generate_key().decode()

    def encrypt_database_connection(self, connection_string: str) -> str:
        """Encrypt database connection string."""
        return self.encrypt_field(connection_string)

    def create_backup_encryption_key(self) -> str:
        """Create separate key for backup encryption."""
        import hashlib
        
        backup_key = hashlib.sha256(
            (self.master_key + '_backup').encode()
        ).hexdigest()
        
        return backup_key


class FieldEncryptionDecorator:
    """Decorator for automatic field encryption on SQLAlchemy models."""

    def __init__(self, encryption_manager: EncryptionManager = None):
        self.encryption_manager = encryption_manager or EncryptionManager()

    def encrypt_on_save(self, model, fields_to_encrypt: list):
        """Encrypt specified fields before saving model."""
        for field_name in fields_to_encrypt:
            if hasattr(model, field_name):
                original_value = getattr(model, field_name)
                if original_value:
                    encrypted_value = self.encryption_manager.encrypt_field(original_value)
                    setattr(model, field_name, encrypted_value)

    def decrypt_on_load(self, model, fields_to_decrypt: list):
        """Decrypt specified fields after loading model."""
        for field_name in fields_to_decrypt:
            if hasattr(model, field_name):
                encrypted_value = getattr(model, field_name)
                if encrypted_value:
                    decrypted_value = self.encryption_manager.decrypt_field(encrypted_value)
                    setattr(model, field_name, decrypted_value)


# Sensitive fields that should be encrypted
FIELDS_TO_ENCRYPT = {
    'User': ['email', 'hashed_password'],
    'Tenant': ['api_key'],
    'ApiKey': ['key_hash'],
}

# Data masking rules for different field types
DATA_MASKING_RULES = {
    'email': 'email',
    'phone': 'phone',
    'password': 'generic',
    'api_key': 'generic',
    'card_number': 'card',
}
