"""
Notification System for Route Master
Handles email, SMS, and push notifications for bookings and alerts.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class NotificationConfig:
    """Email notification configuration"""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = "nagar.industries.routes@gmail.com"
    sender_password: str = "****"
    use_tls: bool = True

class NotificationService:
    """Service for sending notifications"""
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or NotificationConfig()
        self.logger = logger
        
    def send_email(self, recipient: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send email notification"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.sender_email
            msg['To'] = recipient
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # In production, connect to SMTP server
            # For now, just log
            self.logger.info(f"Email sent to {recipient}: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_sms(self, phone: str, message: str) -> bool:
        """Send SMS notification"""
        try:
            # In production, integrate with SMS provider (Twilio, etc.)
            self.logger.info(f"SMS sent to {phone}: {message}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send SMS: {str(e)}")
            return False
    
    def send_push(self, user_id: str, title: str, message: str, data: dict = None) -> bool:
        """Send push notification"""
        try:
            # In production, integrate with push notification service
            self.logger.info(f"Push sent to user {user_id}: {title} - {message}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send push notification: {str(e)}")
            return False
    
    def notify_booking_confirmed(self, user_email: str, booking_details: dict) -> bool:
        """Send booking confirmation notification"""
        subject = f"Booking Confirmed - PNR {booking_details.get('pnr', 'N/A')}"
        
        body = f"""
        Dear Passenger,
        
        Your booking has been confirmed!
        
        Route: {booking_details.get('origin')} to {booking_details.get('destination')}
        Date: {booking_details.get('date')}
        Train: {booking_details.get('train_number')}
        Class: {booking_details.get('class')}
        
        PNR: {booking_details.get('pnr')}
        
        Thank you for using Route Master!
        """
        
        return self.send_email(user_email, subject, body)
    
    def notify_booking_cancelled(self, user_email: str, pnr: str) -> bool:
        """Send booking cancellation notification"""
        subject = f"Booking Cancelled - PNR {pnr}"
        
        body = f"""
        Dear Passenger,
        
        Your booking has been cancelled.
        
        PNR: {pnr}
        Refund will be processed within 5-7 business days.
        
        Thank you for using Route Master!
        """
        
        return self.send_email(user_email, subject, body)
    
    def notify_price_drop(self, user_email: str, route_details: dict, old_price: float, new_price: float) -> bool:
        """Notify user of price drop on tracked route"""
        subject = f"Price Drop Alert - {route_details.get('origin')} to {route_details.get('destination')}"
        
        body = f"""
        Great News!
        
        The price for {route_details.get('origin')} to {route_details.get('destination')} has dropped!
        
        Old Price: ₹{old_price}
        New Price: ₹{new_price}
        Savings: ₹{old_price - new_price}
        
        Book now at the new price!
        """
        
        return self.send_email(user_email, subject, body)
    
    def notify_train_delay(self, user_email: str, train_number: str, delay_minutes: int) -> bool:
        """Notify user of train delay"""
        subject = f"Train Delay Alert - {train_number}"
        
        body = f"""
        Update: Train {train_number} is running {delay_minutes} minutes late.
        
        Please check the status for latest information.
        """
        
        return self.send_email(user_email, subject, body)

# Global notification service instance
_notification_service: Optional[NotificationService] = None

def get_notification_service() -> NotificationService:
    """Get or create notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service

# Export main class
__all__ = ['NotificationService', 'NotificationConfig', 'get_notification_service']
