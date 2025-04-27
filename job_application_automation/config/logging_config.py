"""
Logging configuration for the job application automation system.
Enhanced with centralized configuration management.
"""
import os
import logging
import logging.config
import structlog
from typing import Dict, Any
from pythonjsonlogger import jsonlogger
from logging.handlers import RotatingFileHandler
from .config import get_config

def configure_logging():
    """Configure logging based on the centralized configuration."""
    config = get_config()
    log_config = config.logging
    
    # Create log directory
    os.makedirs(log_config.log_dir, exist_ok=True)
    
    # Determine log level
    log_level = getattr(logging, log_config.level)
    
    # Configure handlers
    handlers = {}
    
    if log_config.console_logging:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        }
    
    if log_config.file_logging:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "json" if log_config.log_format == "json" else "standard",
            "filename": os.path.join(log_config.log_dir, "application.log"),
            "maxBytes": log_config.max_size_mb * 1024 * 1024,
            "backupCount": log_config.backup_count
        }
        
        handlers["error_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "json" if log_config.log_format == "json" else "standard", 
            "filename": os.path.join(log_config.log_dir, "error.log"),
            "maxBytes": log_config.max_size_mb * 1024 * 1024,
            "backupCount": log_config.backup_count
        }
        
        handlers["audit_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": os.path.join(log_config.log_dir, "audit.log"),
            "maxBytes": log_config.max_size_mb * 1024 * 1024,
            "backupCount": log_config.backup_count
        }
    
    # Configure logging with handlers
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": log_config.format
            },
            "json": {
                "()": jsonlogger.JsonFormatter,
                "fmt": "%(asctime)s %(name)s %(levelname)s %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": handlers,
        "loggers": {
            "": {  # Root logger
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": True
            },
            "job_application_automation": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": False
            },
            "job_application_automation.audit": {
                "handlers": ["audit_file"] if "audit_file" in handlers else list(handlers.keys()),
                "level": "INFO",
                "propagate": False
            }
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(logging_config)
    
    # Configure structlog
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    
    # Add JSON renderer for file logging
    if log_config.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    return logging.getLogger("job_application_automation")


class AuditLogger:
    """Logger for tracking important application events."""
    
    def __init__(self):
        self.logger = logging.getLogger("job_application_automation.audit")
        
    def log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log an application event with structured details.
        
        Args:
            event_type: Type of event (e.g., 'application_create', 'security_warning')
            details: Dictionary with event details
        """
        self.logger.info(f"Event: {event_type}", 
                        extra={"event_type": event_type, **details})
        
    def log_application_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log an application-related event."""
        self.log_event(f"application.{event_type}", details)
        
    def log_search_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log a job search-related event."""
        self.log_event(f"search.{event_type}", details)
        
    def log_error_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log an error event."""
        self.logger.error(f"Error: {event_type}", 
                         extra={"event_type": f"error.{event_type}", **details})
        
    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log a security-related event."""
        self.logger.warning(f"Security: {event_type}", 
                          extra={"event_type": f"security.{event_type}", **details})


# Initialize logging when this module is imported
logger = configure_logging()