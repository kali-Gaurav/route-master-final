# core/password_policy.py
"""Password Policy Enforcement"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PasswordStrength(Enum):
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"
    VERY_STRONG = "very_strong"

@dataclass
class PasswordPolicy:
    """Password policy configuration"""
    min_length: int = 8
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special_chars: bool = True
    prevent_common_passwords: bool = True
    prevent_personal_info: bool = False
    max_consecutive_chars: int = 3
    min_unique_chars: int = 6

    # Common weak passwords to reject
    common_passwords = {
        "password", "123456", "123456789", "qwerty", "abc123", "password123",
        "admin", "letmein", "welcome", "monkey", "dragon", "passw0rd",
        "12345678", "qwerty123", "admin123", "root", "user", "guest"
    }

class PasswordPolicyViolation(Exception):
    """Exception raised when password violates policy"""
    def __init__(self, violations: List[str]):
        self.violations = violations
        super().__init__(f"Password policy violations: {', '.join(violations)}")

class PasswordPolicyValidator:
    """Validate passwords against security policies"""

    def __init__(self, policy: Optional[PasswordPolicy] = None):
        self.policy = policy or PasswordPolicy()

    def validate_password(self, password: str, user_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate password against policy

        Args:
            password: Password to validate
            user_info: Optional user information for personal info checks

        Returns:
            Dict with 'valid': bool and 'violations': List[str]
        """
        violations = []

        # Length checks
        if len(password) < self.policy.min_length:
            violations.append(f"Password must be at least {self.policy.min_length} characters long")

        if len(password) > self.policy.max_length:
            violations.append(f"Password must be no more than {self.policy.max_length} characters long")

        # Character requirements
        if self.policy.require_uppercase and not re.search(r'[A-Z]', password):
            violations.append("Password must contain at least one uppercase letter")

        if self.policy.require_lowercase and not re.search(r'[a-z]', password):
            violations.append("Password must contain at least one lowercase letter")

        if self.policy.require_digits and not re.search(r'\d', password):
            violations.append("Password must contain at least one digit")

        if self.policy.require_special_chars and not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            violations.append("Password must contain at least one special character")

        # Unique characters check
        unique_chars = len(set(password))
        if unique_chars < self.policy.min_unique_chars:
            violations.append(f"Password must contain at least {self.policy.min_unique_chars} unique characters")

        # Consecutive characters check
        if self._has_consecutive_chars(password, self.policy.max_consecutive_chars):
            violations.append(f"Password must not contain more than {self.policy.max_consecutive_chars} consecutive identical characters")

        # Common passwords check
        if self.policy.prevent_common_passwords and password.lower() in self.policy.common_passwords:
            violations.append("Password is too common and easily guessable")

        # Personal information check
        if self.policy.prevent_personal_info and user_info:
            if self._contains_personal_info(password, user_info):
                violations.append("Password must not contain personal information")

        # Calculate strength
        strength = self._calculate_strength(password, violations)

        return {
            'valid': len(violations) == 0,
            'violations': violations,
            'strength': strength.value,
            'score': self._get_strength_score(strength)
        }

    def _has_consecutive_chars(self, password: str, max_consecutive: int) -> bool:
        """Check for consecutive identical characters"""
        count = 1
        for i in range(1, len(password)):
            if password[i] == password[i-1]:
                count += 1
                if count > max_consecutive:
                    return True
            else:
                count = 1
        return False

    def _contains_personal_info(self, password: str, user_info: Dict[str, Any]) -> bool:
        """Check if password contains personal information"""
        password_lower = password.lower()

        # Check common personal info fields
        personal_fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'birth_date']

        for field in personal_fields:
            value = user_info.get(field)
            if value and str(value).lower() in password_lower:
                return True

        return False

    def _calculate_strength(self, password: str, violations: List[str]) -> PasswordStrength:
        """Calculate password strength"""
        score = 0

        # Length scoring
        if len(password) >= 12:
            score += 2
        elif len(password) >= 8:
            score += 1

        # Character variety scoring
        char_types = 0
        if re.search(r'[A-Z]', password): char_types += 1
        if re.search(r'[a-z]', password): char_types += 1
        if re.search(r'\d', password): char_types += 1
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password): char_types += 1

        score += char_types

        # Uniqueness scoring
        if len(password) > 0:
            unique_ratio = len(set(password)) / len(password)
        else:
            unique_ratio = 0
        if unique_ratio > 0.8:
            score += 2
        elif unique_ratio > 0.6:
            score += 1

        # Penalty for violations
        score -= len(violations)

        # Determine strength
        if score >= 6:
            return PasswordStrength.VERY_STRONG
        elif score >= 4:
            return PasswordStrength.STRONG
        elif score >= 2:
            return PasswordStrength.MEDIUM
        else:
            return PasswordStrength.WEAK

    def _get_strength_score(self, strength: PasswordStrength) -> int:
        """Get numerical score for password strength"""
        scores = {
            PasswordStrength.WEAK: 1,
            PasswordStrength.MEDIUM: 2,
            PasswordStrength.STRONG: 3,
            PasswordStrength.VERY_STRONG: 4
        }
        return scores[strength]

    def get_policy_requirements(self) -> Dict[str, Any]:
        """Get current policy requirements for display"""
        return {
            'min_length': self.policy.min_length,
            'max_length': self.policy.max_length,
            'require_uppercase': self.policy.require_uppercase,
            'require_lowercase': self.policy.require_lowercase,
            'require_digits': self.policy.require_digits,
            'require_special_chars': self.policy.require_special_chars,
            'min_unique_chars': self.policy.min_unique_chars,
            'max_consecutive_chars': self.policy.max_consecutive_chars,
            'prevent_common_passwords': self.policy.prevent_common_passwords,
            'prevent_personal_info': self.policy.prevent_personal_info
        }

# Global instance with default policy
password_validator = PasswordPolicyValidator()