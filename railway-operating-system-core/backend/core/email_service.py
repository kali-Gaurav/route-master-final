# core/email_service.py
"""Email Service for Verification and Notifications"""

import smtplib
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import redis
import json
from dataclasses import dataclass

from ..config import settings

logger = logging.getLogger(__name__)

@dataclass
class EmailConfig:
    """Email configuration"""
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    from_email: str
    from_name: str
    use_tls: bool = True

class EmailVerificationToken:
    """Email verification token management"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.token_expiry = 24 * 60 * 60  # 24 hours

    def generate_token(self, email: str) -> str:
        """Generate verification token for email"""
        token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

        token_data = {
            'email': email,
            'created_at': datetime.utcnow().isoformat(),
            'token': token
        }

        if self.redis:
            try:
                key = f"email_verification:{token}"
                self.redis.setex(key, self.token_expiry, json.dumps(token_data))
            except Exception as e:
                logger.warning(f"Failed to store verification token in Redis: {e}")

        return token

    def verify_token(self, token: str) -> Optional[str]:
        """Verify token and return email if valid"""
        if not self.redis:
            return None

        try:
            key = f"email_verification:{token}"
            data = self.redis.get(key)

            if not data:
                return None

            token_data = json.loads(data)
            email = token_data.get('email')

            # Delete token after successful verification
            self.redis.delete(key)

            return email

        except Exception as e:
            logger.error(f"Failed to verify email token: {e}")
            return None

class EmailService:
    """Service for sending emails"""

    def __init__(self, config: EmailConfig, redis_client: Optional[redis.Redis] = None):
        self.config = config
        self.token_manager = EmailVerificationToken(redis_client)

    def _create_smtp_connection(self):
        """Create SMTP connection"""
        try:
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls() if self.config.use_tls else None
            server.login(self.config.smtp_username, self.config.smtp_password)
            return server
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise

    def send_verification_email(self, email: str, verification_url: str) -> bool:
        """Send email verification link"""
        try:
            token = self.token_manager.generate_token(email)

            subject = "Verify Your Railway Operating System Account"
            html_content = f"""
            <html>
            <body>
                <h2>Welcome to Railway Operating System!</h2>
                <p>Please verify your email address by clicking the link below:</p>
                <p><a href="{verification_url}?token={token}">Verify Email Address</a></p>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't create an account, please ignore this email.</p>
                <br>
                <p>Best regards,<br>Railway Operating System Team</p>
            </body>
            </html>
            """

            text_content = f"""
            Welcome to Railway Operating System!

            Please verify your email address by visiting: {verification_url}?token={token}

            This link will expire in 24 hours.

            If you didn't create an account, please ignore this email.

            Best regards,
            Railway Operating System Team
            """

            return self._send_email(email, subject, text_content, html_content)

        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {e}")
            return False

    def send_password_reset_email(self, email: str, reset_url: str) -> bool:
        """Send password reset email"""
        try:
            token = self.token_manager.generate_token(email)

            subject = "Reset Your Railway Operating System Password"
            html_content = f"""
            <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>You requested a password reset for your Railway Operating System account.</p>
                <p>Click the link below to reset your password:</p>
                <p><a href="{reset_url}?token={token}">Reset Password</a></p>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't request this reset, please ignore this email.</p>
                <br>
                <p>Best regards,<br>Railway Operating System Team</p>
            </body>
            </html>
            """

            text_content = f"""
            Password Reset Request

            You requested a password reset for your Railway Operating System account.

            Visit this link to reset your password: {reset_url}?token={token}

            This link will expire in 24 hours.

            If you didn't request this reset, please ignore this email.

            Best regards,
            Railway Operating System Team
            """

            return self._send_email(email, subject, text_content, html_content)

        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")
            return False

    def send_welcome_email(self, email: str, user_name: str) -> bool:
        """Send welcome email after verification"""
        try:
            subject = "Welcome to Railway Operating System!"
            html_content = f"""
            <html>
            <body>
                <h2>Welcome aboard, {user_name}!</h2>
                <p>Your email has been verified and your account is now active.</p>
                <p>You can now log in to the Railway Operating System and start managing routes and operations.</p>
                <br>
                <p>Best regards,<br>Railway Operating System Team</p>
            </body>
            </html>
            """

            text_content = f"""
            Welcome aboard, {user_name}!

            Your email has been verified and your account is now active.

            You can now log in to the Railway Operating System and start managing routes and operations.

            Best regards,
            Railway Operating System Team
            """

            return self._send_email(email, subject, text_content, html_content)

        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {e}")
            return False

    def _send_email(self, to_email: str, subject: str, text_content: str, html_content: str) -> bool:
        """Send email with both text and HTML content"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = to_email

            # Attach parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')

            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
            with self._create_smtp_connection() as server:
                server.sendmail(self.config.from_email, to_email, msg.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def verify_email_token(self, token: str) -> Optional[str]:
        """Verify email verification token"""
        return self.token_manager.verify_token(token)

# Global email service instance
email_service = None

def get_email_service() -> EmailService:
    """Get email service instance"""
    global email_service
    if email_service is None:
        # Email configuration from environment
        email_config = EmailConfig(
            smtp_server=settings.smtp_server,
            smtp_port=settings.smtp_port,
            smtp_username=settings.smtp_username,
            smtp_password=settings.smtp_password,
            from_email=settings.from_email,
            from_name=settings.from_name,
            use_tls=settings.smtp_use_tls
        )

        # Try to get Redis client
        redis_client = None
        try:
            import redis
            redis_client = redis.from_url(settings.redis_url)
        except:
            pass

        email_service = EmailService(email_config, redis_client)

    return email_service