"""
Alerting & Notification System

Monitors system health and sends alerts when:
- >20% of trains become inactive
- API failure rate exceeds 10%
- Data freshness score < 60%
- Database backup fails
- Validation errors exceed threshold

Supports: Email, Webhook, Dashboard
"""

import json
import smtplib
import requests
from datetime import datetime
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, asdict

from config import ALERTS, LOGGING_CONFIG
from logger import LoggerFactory, audit_logger

alert_logger = LoggerFactory.get_logger("alerting_system")


@dataclass
class Alert:
    """Alert notification"""
    timestamp: datetime
    severity: str  # CRITICAL, WARNING, INFO
    alert_type: str  # INACTIVE_TRAINS, API_FAILURE, DATA_FRESHNESS, etc.
    title: str
    message: str
    details: Dict
    threshold: float = 0.0
    actual_value: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity,
            "alert_type": self.alert_type,
            "title": self.title,
            "message": self.message,
            "threshold": self.threshold,
            "actual_value": self.actual_value,
            "details": self.details
        }


class AlertingSystem:
    """Main alerting system"""
    
    def __init__(self):
        self.logger = LoggerFactory.get_logger("alerting_system")
        self.config = ALERTS
        self.alert_history: List[Alert] = []
        self.email_enabled = self.config.get("enable_email_alerts", False)
        self.webhook_enabled = self.config.get("enable_webhook_alerts", False)
    
    def check_inactive_trains_threshold(self, total_trains: int,
                                       inactive_trains: int) -> Optional[Alert]:
        """
        Check if too many trains are inactive
        
        Args:
            total_trains: Total number of trains
            inactive_trains: Number of inactive trains
        
        Returns:
            Alert object if threshold exceeded
        """
        if total_trains == 0:
            return None
        
        inactive_percentage = inactive_trains / total_trains
        threshold = self.config.get("inactive_train_percentage_threshold", 0.2)
        
        if inactive_percentage > threshold:
            alert = Alert(
                timestamp=datetime.utcnow(),
                severity="CRITICAL" if inactive_percentage > 0.3 else "WARNING",
                alert_type="INACTIVE_TRAINS",
                title=f"{inactive_percentage*100:.1f}% of trains are inactive",
                message=f"{inactive_trains} out of {total_trains} trains marked as INACTIVE. "
                        f"Threshold: {threshold*100:.1f}%",
                details={
                    "total_trains": total_trains,
                    "inactive_trains": inactive_trains,
                    "inactive_percentage": inactive_percentage,
                    "threshold_percentage": threshold
                },
                threshold=threshold,
                actual_value=inactive_percentage
            )
            
            self.logger.warning(alert.message, extra=alert.to_dict())
            return alert
        
        return None
    
    def check_api_failure_rate(self, total_requests: int,
                              failed_requests: int) -> Optional[Alert]:
        """Check API failure rate"""
        if total_requests == 0:
            return None
        
        failure_rate = failed_requests / total_requests
        threshold = self.config.get("api_failure_rate_threshold", 0.1)
        
        if failure_rate > threshold:
            alert = Alert(
                timestamp=datetime.utcnow(),
                severity="CRITICAL" if failure_rate > 0.25 else "WARNING",
                alert_type="API_FAILURE",
                title=f"API failure rate at {failure_rate*100:.1f}%",
                message=f"API failed {failed_requests} out of {total_requests} requests. "
                        f"Threshold: {threshold*100:.1f}%",
                details={
                    "total_requests": total_requests,
                    "failed_requests": failed_requests,
                    "failure_rate": failure_rate,
                    "threshold_rate": threshold
                },
                threshold=threshold,
                actual_value=failure_rate
            )
            
            self.logger.warning(alert.message, extra=alert.to_dict())
            audit_logger.log_error_event(
                error_type="API_FAILURE_ALERT",
                message=alert.message,
                context=alert.details,
                severity="WARNING"
            )
            return alert
        
        return None
    
    def check_data_freshness(self, freshness_score: float) -> Optional[Alert]:
        """Check overall data freshness score"""
        threshold = self.config.get("data_freshness_score_threshold", 0.6)
        
        if freshness_score < threshold:
            alert = Alert(
                timestamp=datetime.utcnow(),
                severity="WARNING",
                alert_type="DATA_FRESHNESS",
                title=f"Data freshness low: {freshness_score*100:.1f}%",
                message=f"Data freshness score is {freshness_score*100:.1f}%. "
                        f"Target: {threshold*100:.1f}%. "
                        f"Consider running refresh operation.",
                details={
                    "freshness_score": freshness_score,
                    "threshold_score": threshold,
                    "recommended_action": "Run refresh_engine to update stale data"
                },
                threshold=threshold,
                actual_value=freshness_score
            )
            
            self.logger.warning(alert.message, extra=alert.to_dict())
            return alert
        
        return None
    
    def check_validation_errors(self, error_count: int,
                               max_allowed: int = 100) -> Optional[Alert]:
        """Check for excessive validation errors"""
        if error_count > max_allowed:
            alert = Alert(
                timestamp=datetime.utcnow(),
                severity="CRITICAL",
                alert_type="VALIDATION_ERRORS",
                title=f"High validation error count: {error_count}",
                message=f"Data validation reported {error_count} errors. "
                        f"Maximum allowed: {max_allowed}. "
                        f"Review validation_report.json for details.",
                details={
                    "error_count": error_count,
                    "max_allowed": max_allowed,
                    "recommended_action": "Check validation_report.json and investigate data quality"
                },
                threshold=max_allowed,
                actual_value=error_count
            )
            
            self.logger.error(alert.message, extra=alert.to_dict())
            audit_logger.log_error_event(
                error_type="VALIDATION_ERROR_ALERT",
                message=alert.message,
                context=alert.details,
                severity="CRITICAL"
            )
            return alert
        
        return None
    
    def send_alert(self, alert: Alert):
        """Send alert via configured channels"""
        # Store in history
        self.alert_history.append(alert)
        
        # Send email
        if self.email_enabled:
            self._send_email_alert(alert)
        
        # Send webhook
        if self.webhook_enabled:
            self._send_webhook_alert(alert)
    
    def _send_email_alert(self, alert: Alert):
        """Send alert via email"""
        try:
            recipients = self.config.get("alert_email_recipients", [])
            if not recipients:
                self.logger.warning("No email recipients configured")
                return
            
            # Create email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[{alert.severity}] {alert.title}"
            msg["From"] = "railway-alerts@system.local"
            msg["To"] = ", ".join(recipients)
            
            # Plain text version
            text_body = f"""{alert.title}
Severity: {alert.severity}
Time: {alert.timestamp.isoformat()}

Message:
{alert.message}

Details:
{json.dumps(alert.details, indent=2)}
"""
            
            # HTML version
            html_body = f"""
<html>
  <body>
    <h2>{alert.title}</h2>
    <p><strong>Severity:</strong> {alert.severity}</p>
    <p><strong>Time:</strong> {alert.timestamp.isoformat()}</p>
    <hr>
    <p>{alert.message}</p>
    <h3>Details:</h3>
    <pre>{json.dumps(alert.details, indent=2)}</pre>
  </body>
</html>
"""
            
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            # Note: Actual email sending requires SMTP configuration
            self.logger.info(
                f"Alert email prepared (not sent - SMTP not configured)",
                extra={
                    "recipients": recipients,
                    "subject": msg["Subject"]
                }
            )
        
        except Exception as e:
            self.logger.error(f"Failed to prepare email alert: {e}", exc_info=True)
    
    def _send_webhook_alert(self, alert: Alert):
        """Send alert via webhook"""
        try:
            webhook_url = self.config.get("webhook_url")
            if not webhook_url:
                self.logger.warning("No webhook URL configured")
                return
            
            # Prepare payload
            payload = {
                "timestamp": alert.timestamp.isoformat(),
                "severity": alert.severity,
                "alert_type": alert.alert_type,
                "title": alert.title,
                "message": alert.message,
                "details": alert.details
            }
            
            # Send webhook
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.logger.info(
                    f"Webhook alert sent successfully",
                    extra={"url": webhook_url, "status": response.status_code}
                )
            else:
                self.logger.warning(
                    f"Webhook alert returned status {response.status_code}",
                    extra={"url": webhook_url, "status": response.status_code}
                )
        
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}", exc_info=True)
    
    def get_alert_history(self, limit: int = 100) -> List[Dict]:
        """Get recent alert history"""
        return [a.to_dict() for a in self.alert_history[-limit:]]
    
    def clear_alert_history(self):
        """Clear alert history"""
        self.alert_history.clear()
        self.logger.info("Alert history cleared")


# Global alerting system instance
alertingSystem = AlertingSystem()
