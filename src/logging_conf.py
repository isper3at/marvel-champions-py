"""
Centralized logging configuration.

Provides:
- Application logging (INFO level by default)
- Debug logging (DEBUG level in development)
- Audit logging (user actions on endpoints)
"""

from pathlib import Path
from typing import Optional
import logging
import logging.handlers
import datetime
import json


# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


class AuditLogger:
    """
    Audit logger for tracking user actions.
    
    Logs to separate audit log file with structured format.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # Don't propagate to root logger
        
        # Audit log file with rotation
        audit_handler = logging.handlers.RotatingFileHandler(
            LOGS_DIR / "audit.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        
        # JSON formatter for structured logs
        audit_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(audit_handler)
    
    def log_action(
        self,
        action: str,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[dict] = None
    ):
        """
        Log a user action.
        
        Args:
            action: Action performed (e.g., "import_deck", "create_game")
            user_id: User identifier (session ID, username, etc.)
            endpoint: API endpoint called
            method: HTTP method (GET, POST, etc.)
            status_code: Response status code
            details: Additional context as dict
        """
        self.logger.info(
            "audit",
            extra={
                "action": action,
                "user_id": user_id or "anonymous",
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "details": details or {},
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
            }
        )


class JsonFormatter(logging.Formatter):
    """Format log records as JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields
        if hasattr(record, "action"):
            log_data["action"] = record.action
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "details"):
            log_data["details"] = record.details
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Add colors to console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logging(debug: bool = False):
    """
    Configure application logging.
    
    Args:
        debug: If True, set DEBUG level. Otherwise INFO level.
    """
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Debug file handler (only in debug mode)
    if debug:
        debug_handler = logging.handlers.RotatingFileHandler(
            LOGS_DIR / "debug.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(file_formatter)
        root_logger.addHandler(debug_handler)
    
    # Quiet down noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized (debug={'ON' if debug else 'OFF'})")


# Global audit logger instance
audit_logger = AuditLogger()

