"""
Logging configuration for the job application automation system.
"""
import os
import logging.config
import structlog
from typing import Dict, Any
from pythonjsonlogger import jsonlogger

# Create logs directory if it doesn't exist
os.makedirs("../data/logs", exist_ok=True)

# Common logging configuration
COMMON_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "()": jsonlogger.JsonFormatter,
            "fmt": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": "../data/logs/application.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "json",
            "filename": "../data/logs/error.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        },
        "audit_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": "../data/logs/audit.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True
        },
        "job_application_automation": {
            "handlers": ["console", "file", "error_file"],
            "level": "DEBUG",
            "propagate": False
        },
        "job_application_automation.audit": {
            "handlers": ["audit_file"],
            "level": "INFO",
            "propagate": False
        }
    }
}

# Structured logging setup
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.BoundLogger,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

class AuditLogger:
    """Logger for tracking important application events."""
    
    def __init__(self):
        self.logger = logging.getLogger("job_application_automation.audit")
        
    def log_application_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log an application-related event."""
        self.logger.info(f"Application Event: {event_type}", 
                        extra={"event_type": event_type, **details})
        
    def log_search_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log a job search-related event."""
        self.logger.info(f"Search Event: {event_type}", 
                        extra={"event_type": event_type, **details})
        
    def log_error_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log an error event."""
        self.logger.error(f"Error Event: {event_type}", 
                         extra={"event_type": event_type, **details})
        
    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log a security-related event."""
        self.logger.warning(f"Security Event: {event_type}", 
                          extra={"event_type": event_type, **details})