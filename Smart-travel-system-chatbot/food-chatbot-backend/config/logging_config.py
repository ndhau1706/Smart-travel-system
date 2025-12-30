"""
Logging configuration for Food Chatbot Backend.

Features:
- Structured JSON logging for production
- Console logging for development
- File rotation (10MB max, 5 backups)
- Request ID tracking
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
"""
import os
import sys
import logging
import logging.config
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Get debug mode from environment
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")


class RequestIdFilter(logging.Filter):
    """Add request_id to log records."""
    
    def filter(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = '-'
        if not hasattr(record, 'user_id'):
            record.user_id = '-'
        if not hasattr(record, 'session_id'):
            record.session_id = '-'
        return True


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        import json
        
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add optional fields
        if hasattr(record, 'request_id') and record.request_id != '-':
            log_record["request_id"] = record.request_id
        if hasattr(record, 'user_id') and record.user_id != '-':
            log_record["user_id"] = record.user_id
        if hasattr(record, 'session_id') and record.session_id != '-':
            log_record["session_id"] = record.session_id
        
        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_record)


# Logging configuration dictionary
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "json": {
            "()": JsonFormatter
        }
    },
    
    "filters": {
        "request_id": {
            "()": RequestIdFilter
        }
    },
    
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG" if DEBUG else "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
            "filters": ["request_id"]
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(LOGS_DIR / "app.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
            "filters": ["request_id"]
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "json",
            "filename": str(LOGS_DIR / "error.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
            "filters": ["request_id"]
        },
        "json_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": str(LOGS_DIR / "app.json.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
            "filters": ["request_id"]
        }
    },
    
    "loggers": {
        "": {  # Root logger
            "level": "DEBUG" if DEBUG else "INFO",
            "handlers": ["console", "file", "error_file"],
            "propagate": False
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False
        },
        "uvicorn.access": {
            "level": "WARNING",  # Reduce access log noise
            "handlers": ["console"],
            "propagate": False
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["console", "error_file"],
            "propagate": False
        },
        "fastapi": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False
        },
        "chatbot": {
            "level": "DEBUG" if DEBUG else "INFO",
            "handlers": ["console", "file", "json_file", "error_file"],
            "propagate": False
        },
        "chatbot.rag": {
            "level": "DEBUG" if DEBUG else "INFO",
            "handlers": ["console", "file"],
            "propagate": False
        },
        "chatbot.search": {
            "level": "DEBUG" if DEBUG else "INFO",
            "handlers": ["console", "file"],
            "propagate": False
        },
        "chatbot.auth": {
            "level": "INFO",
            "handlers": ["console", "file", "error_file"],
            "propagate": False
        }
    }
}


def setup_logging():
    """Initialize logging configuration."""
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger("chatbot")
    logger.info("Logging system initialized", extra={
        "debug_mode": DEBUG,
        "log_dir": str(LOGS_DIR)
    })
    return logger


def get_logger(name: str = "chatbot") -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (will be prefixed with 'chatbot.' if not already)
        
    Returns:
        Logger instance
    """
    if not name.startswith("chatbot"):
        name = f"chatbot.{name}"
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding extra context to logs."""
    
    def __init__(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        self.request_id = request_id
        self.user_id = user_id
        self.session_id = session_id
        self._old_factory = None
    
    def __enter__(self):
        self._old_factory = logging.getLogRecordFactory()
        
        request_id = self.request_id
        user_id = self.user_id
        session_id = self.session_id
        old_factory = self._old_factory
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.request_id = request_id or getattr(record, 'request_id', '-')
            record.user_id = user_id or getattr(record, 'user_id', '-')
            record.session_id = session_id or getattr(record, 'session_id', '-')
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self._old_factory)
        return False


# Initialize logging when module is imported
setup_logging()
