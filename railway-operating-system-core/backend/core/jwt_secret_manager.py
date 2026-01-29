# core/jwt_secret_manager.py
"""JWT Secret Management with Key Rotation"""

import os
import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

class JWTSecretManager:
    """Manage JWT secrets with rotation and encryption"""

    def __init__(self, secrets_file: str = "jwt_secrets.json", key_file: str = "master_key.key"):
        self.secrets_file = secrets_file
        self.key_file = key_file
        self._master_key = self._load_or_create_master_key()
        self._cipher = Fernet(self._master_key)
        self._secrets = self._load_secrets()
        self._ensure_active_secret()

    def _load_or_create_master_key(self) -> bytes:
        """Load or create master encryption key"""
        if os.path.exists(self.key_file):
            try:
                with open(self.key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to load master key: {e}")

        # Create new master key
        logger.info("Creating new master encryption key")
        master_key = Fernet.generate_key()
        try:
            with open(self.key_file, 'wb') as f:
                f.write(master_key)
            # Set restrictive permissions
            os.chmod(self.key_file, 0o600)
        except Exception as e:
            logger.error(f"Failed to save master key: {e}")

        return master_key

    def _load_secrets(self) -> Dict:
        """Load encrypted secrets from file"""
        if not os.path.exists(self.secrets_file):
            return {}

        try:
            with open(self.secrets_file, 'r') as f:
                encrypted_data = f.read()

            if encrypted_data:
                decrypted_data = self._cipher.decrypt(encrypted_data.encode())
                return json.loads(decrypted_data.decode())
            else:
                return {}
        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")
            return {}

    def _save_secrets(self):
        """Save secrets encrypted to file"""
        try:
            secrets_json = json.dumps(self._secrets, default=str)
            encrypted_data = self._cipher.encrypt(secrets_json.encode())

            with open(self.secrets_file, 'w') as f:
                f.write(encrypted_data.decode())

            # Set restrictive permissions
            os.chmod(self.secrets_file, 0o600)

        except Exception as e:
            logger.error(f"Failed to save secrets: {e}")

    def _ensure_active_secret(self):
        """Ensure there's always an active secret"""
        if not self._secrets or not any(s.get('active', False) for s in self._secrets.values()):
            self.rotate_secret()
            logger.info("Created initial active JWT secret")

    def rotate_secret(self, keep_previous: bool = True) -> str:
        """Rotate to a new secret, optionally keeping previous ones"""
        new_secret_id = f"secret_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        new_secret = secrets.token_urlsafe(64)  # 512-bit secret

        # Mark all existing secrets as inactive
        for secret_data in self._secrets.values():
            secret_data['active'] = False

        # Add new active secret
        self._secrets[new_secret_id] = {
            'secret': new_secret,
            'created_at': datetime.utcnow(),
            'active': True,
            'expires_at': datetime.utcnow() + timedelta(days=90)  # 90 days validity
        }

        # Remove old secrets if not keeping them
        if not keep_previous:
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            expired_secrets = [
                sid for sid, data in self._secrets.items()
                if data.get('created_at', datetime.min) < cutoff_date and not data.get('active', False)
            ]
            for sid in expired_secrets:
                del self._secrets[sid]

        self._save_secrets()
        logger.info(f"JWT secret rotated: {new_secret_id}")
        return new_secret_id

    def get_active_secret(self) -> Optional[str]:
        """Get the currently active secret"""
        for secret_data in self._secrets.values():
            if secret_data.get('active', False):
                expires_at = secret_data.get('expires_at')
                if expires_at and isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)

                if expires_at and datetime.utcnow() > expires_at:
                    logger.warning("Active JWT secret has expired, rotating...")
                    self.rotate_secret()
                    return self.get_active_secret()  # Recursive call to get new secret

                return secret_data['secret']
        return None

    def get_secret_by_id(self, secret_id: str) -> Optional[str]:
        """Get a specific secret by ID (for validating old tokens)"""
        if secret_id in self._secrets:
            secret_data = self._secrets[secret_id]
            expires_at = secret_data.get('expires_at')
            if expires_at and isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)

            if expires_at and datetime.utcnow() > expires_at:
                return None  # Expired

            return secret_data['secret']
        return None

    def validate_secret(self, secret: str) -> Tuple[bool, Optional[str]]:
        """Validate if a secret is known and return its ID"""
        for secret_id, secret_data in self._secrets.items():
            if secret_data['secret'] == secret:
                expires_at = secret_data.get('expires_at')
                if expires_at and isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)

                if expires_at and datetime.utcnow() > expires_at:
                    return False, None  # Expired

                return True, secret_id
        return False, None

    def get_secret_ids(self) -> list:
        """Get list of all secret IDs (for token validation)"""
        return list(self._secrets.keys())

    def cleanup_expired_secrets(self) -> int:
        """Clean up expired secrets"""
        cutoff_date = datetime.utcnow() - timedelta(days=365)  # Keep for 1 year
        expired_count = 0

        secrets_to_remove = []
        for secret_id, secret_data in self._secrets.items():
            expires_at = secret_data.get('expires_at')
            if expires_at and isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)

            if (expires_at and datetime.utcnow() > expires_at) or \
               (secret_data.get('created_at', datetime.min) < cutoff_date and not secret_data.get('active', False)):
                secrets_to_remove.append(secret_id)
                expired_count += 1

        for secret_id in secrets_to_remove:
            del self._secrets[secret_id]

        if expired_count > 0:
            self._save_secrets()
            logger.info(f"Cleaned up {expired_count} expired JWT secrets")

        return expired_count

# Global instance
jwt_secret_manager = JWTSecretManager()