"""
Logging & Observability Framework

Provides structured JSON logging with:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR)
- File rotation and retention
- Contextual information (request_id, user_id, etc.)
- Performance tracking
- Error tracking and debugging
"""

import logging
import logging.handlers
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from functools import wraps
import time
import sys

from config import LOGGING_CONFIG, LOGS_DIR


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in ["name", "msg", "args", "created", "filename", "funcName", 
                              "levelname", "levelno", "lineno", "module", "msecs", 
                              "message", "pathname", "process", "processName", "relativeCreated",
                              "thread", "threadName", "exc_info", "exc_text", "stack_info"]:
                    try:
                        # Ensure value is JSON serializable
                        json.dumps(value)
                        log_data[key] = value
                    except (TypeError, ValueError):
                        log_data[key] = str(value)
        
        return json.dumps(log_data)


class StandardFormatter(logging.Formatter):
    """Standard human-readable formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as human-readable text"""
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            return (f"[{record.levelname}] {record.name} - {record.getMessage()}\n{exc_text}")
        return f"[{record.levelname}] {record.name} - {record.getMessage()}"


class LoggerFactory:
    """Factory for creating configured loggers"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get or create a logger with the specified name"""
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(LOGGING_CONFIG["level"])
        
        # Remove existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LOGGING_CONFIG["level"])
        
        if LOGGING_CONFIG["format"] == "json":
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(StandardFormatter())
        
        logger.addHandler(console_handler)
        
        # File handler with rotation
        log_file = LOGS_DIR / f"{name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=LOGGING_CONFIG["max_file_size_mb"] * 1024 * 1024,
            backupCount=LOGGING_CONFIG["backup_count"]
        )
        file_handler.setLevel(LOGGING_CONFIG["level"])
        
        if LOGGING_CONFIG["format"] == "json":
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(StandardFormatter())
        
        logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        cls._loggers[name] = logger
        return logger


def log_execution(logger: Optional[logging.Logger] = None, 
                 log_result: bool = True,
                 log_args: bool = False):
    """
    Decorator to log function execution with timing
    
    Args:
        logger: Logger instance to use
        log_result: Whether to log the result
        log_args: Whether to log function arguments
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = LoggerFactory.get_logger(__name__)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = f"{func.__module__}.{func.__name__}"
            
            # Log function call
            log_data = {"action": "function_call", "function": func_name}
            if log_args:
                log_data["args"] = str(args)
                log_data["kwargs"] = str(kwargs)
            
            logger.debug("Function called", extra=log_data)
            
            try:
                result = func(*args, **kwargs)
                
                elapsed_ms = (time.time() - start_time) * 1000
                log_data = {
                    "action": "function_success",
                    "function": func_name,
                    "elapsed_ms": elapsed_ms
                }
                
                if log_result:
                    log_data["result"] = str(result)
                
                logger.info("Function completed", extra=log_data)
                return result
            
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Function failed: {str(e)}",
                    extra={
                        "action": "function_error",
                        "function": func_name,
                        "elapsed_ms": elapsed_ms,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


class AuditLogger:
    """
    Dedicated audit logger for critical operations
    Used for compliance and debugging
    """
    
    def __init__(self):
        self.logger = LoggerFactory.get_logger("audit")
    
    def log_api_call(self, api_name: str, method: str, endpoint: str, 
                    status_code: int, response_time_ms: float, 
                    records_count: int = 0, error: Optional[str] = None):
        """Log API call for audit"""
        self.logger.info(
            f"API call: {api_name}",
            extra={
                "audit_type": "api_call",
                "api_name": api_name,
                "method": method,
                "endpoint": endpoint,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "records_count": records_count,
                "error": error
            }
        )
    
    def log_data_fetch(self, train_no: str, status: str, data_size_bytes: int,
                      response_time_ms: float, timestamp: Optional[datetime] = None):
        """Log data fetch operation"""
        self.logger.info(
            f"Data fetch: {train_no}",
            extra={
                "audit_type": "data_fetch",
                "train_no": train_no,
                "status": status,
                "data_size_bytes": data_size_bytes,
                "response_time_ms": response_time_ms,
                "timestamp": timestamp or datetime.utcnow().isoformat()
            }
        )
    
    def log_data_validation(self, operation: str, records_checked: int,
                           errors_found: int, warnings: int = 0):
        """Log data validation"""
        self.logger.info(
            f"Data validation: {operation}",
            extra={
                "audit_type": "data_validation",
                "operation": operation,
                "records_checked": records_checked,
                "errors_found": errors_found,
                "warnings": warnings
            }
        )
    
    def log_data_modification(self, operation: str, table: str, 
                            records_affected: int, changes: Dict[str, Any]):
        """Log data modifications"""
        self.logger.warning(
            f"Data modification: {operation} on {table}",
            extra={
                "audit_type": "data_modification",
                "operation": operation,
                "table": table,
                "records_affected": records_affected,
                "changes": changes
            }
        )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events"""
        self.logger.warning(
            f"Security event: {event_type}",
            extra={
                "audit_type": "security_event",
                "event_type": event_type,
                **details
            }
        )
    
    def log_error_event(self, error_type: str, message: str, 
                       context: Dict[str, Any], severity: str = "ERROR"):
        """Log error events"""
        self.logger.error(
            f"{error_type}: {message}",
            extra={
                "audit_type": "error_event",
                "error_type": error_type,
                "message": message,
                "severity": severity,
                **context
            }
        )


# Global audit logger instance
audit_logger = AuditLogger()


# Initialize main logger
logger = LoggerFactory.get_logger("railway_dataset")
logger.info("Logging system initialized", extra={"log_format": LOGGING_CONFIG["format"]})
