"""
Logging service for Marvel Champions with verbosity levels,
file storage, and MongoDB redundancy.
"""

import logging
import sys
import os
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import json
import atexit
from pymongo import MongoClient

class LogLevel(Enum):
    """Verbosity levels for logging"""
    DEBUG = logging.DEBUG        # 10 - Detailed diagnostic info
    INFO = logging.INFO          # 20 - General informational messages
    WARNING = logging.WARNING    # 30 - Warning messages
    ERROR = logging.ERROR        # 40 - Error messages
    CRITICAL = logging.CRITICAL  # 50 - Critical errors


class LoggingService:
    """
    Centralized logging service with multiple backends:
    - Console output (with verbosity control)
    - File storage (rolling logs)
    - MongoDB redundancy (automatic sync on shutdown)
    """
    
    def __init__(self, 
                 app_name: str = "marvel-champions",
                 verbosity: LogLevel = LogLevel.INFO,
                 log_dir: str = "logs",
                 mongo_connection: Optional[str] = None,
                 mongo_database: str = "marvel_champions",
                 mongo_collection: str = "logs"):
        """
        Initialize the logging service.
        
        Args:
            app_name: Name of the application
            verbosity: Logging verbosity level
            log_dir: Directory to store log files
            mongo_connection: MongoDB connection string (optional)
            mongo_database: MongoDB database name
            mongo_collection: MongoDB collection name for logs
        """
        self.app_name = app_name
        self.verbosity = verbosity if isinstance(verbosity, LogLevel) else LogLevel(verbosity)
        self.log_dir = log_dir
        self.mongo_connection = mongo_connection
        self.mongo_database = mongo_database
        self.mongo_collection = mongo_collection
        self.db = None
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_buffer = []  # Buffer logs for batch write to Mongo
        self.log_file = None
        
        # Create log directory if needed
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Setup Python logger
        self.python_logger = logging.getLogger(app_name)
        self.python_logger.setLevel(self.verbosity.value)
        
        # Console handler with formatted output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.verbosity.value)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)-8s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        self.python_logger.addHandler(console_handler)
        
        # File handler (append mode)
        log_file_path = os.path.join(log_dir, f"{app_name}_{self.session_id}.log")
        try:
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(LogLevel.DEBUG.value)  # Always log everything to file
            file_handler.setFormatter(formatter)
            self.python_logger.addHandler(file_handler)
            self.log_file = log_file_path
            self.debug(f"Logging initialized: {log_file_path}")
        except Exception as e:
            self.error(f"Failed to setup file logging: {e}")
        
        # Setup MongoDB connection if provided
        if mongo_connection:
            try:
                client = MongoClient(mongo_connection, serverSelectionTimeoutMS=5000)
                client.admin.command('ping')
                self.db = client[mongo_database]
                self.debug(f"MongoDB connection established: {mongo_database}.{mongo_collection}")
            except Exception as e:
                self.warning(f"MongoDB connection failed (logs will only be file-backed): {e}")
        
        # Register shutdown handler to persist logs
        atexit.register(self._on_shutdown)
    
    def debug(self, message: str, **kwargs):
        """Log a debug message"""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log an info message"""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log a warning message"""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log an error message"""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log a critical message"""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def _log(self, level: LogLevel, message: str, **kwargs):
        """Internal log method"""
        # Log to Python logger
        self.python_logger.log(level.value, message)
        
        # Buffer for MongoDB
        if self.db:
            log_entry = {
                'timestamp': datetime.utcnow(),
                'session_id': self.session_id,
                'level': level.name,
                'message': message,
                'app_name': self.app_name,
                **kwargs  # Include any additional context
            }
            self.log_buffer.append(log_entry)
    
    def _on_shutdown(self):
        """Called on application shutdown to persist logs to MongoDB"""
        if self.db and self.log_buffer:
            try:
                collection = self.db[self.mongo_collection]
                collection.insert_many(self.log_buffer)
                self.python_logger.info(
                    f"Persisted {len(self.log_buffer)} log entries to MongoDB"
                )
            except Exception as e:
                self.python_logger.error(
                    f"Failed to persist logs to MongoDB: {e}"
                )
        
        # Log session summary to file
        if self.log_file:
            try:
                with open(self.log_file, 'a') as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Session ended at {datetime.now().isoformat()}\n")
                    f.write(f"Total buffered logs: {len(self.log_buffer)}\n")
                    f.write(f"{'='*60}\n")
            except Exception:
                pass
    
    def get_recent_logs(self, limit: int = 100, level: Optional[str] = None) -> list:
        """Retrieve recent logs from MongoDB"""
        if not self.db:
            return []
        
        try:
            collection = self.db[self.mongo_collection]
            query = {'session_id': self.session_id}
            if level:
                query['level'] = level
            
            logs = list(collection.find(query).sort('_id', -1).limit(limit))
            # Convert ObjectId to string for JSON serialization
            for log in logs:
                log['_id'] = str(log['_id'])
            return logs
        except Exception as e:
            self.error(f"Failed to retrieve logs from MongoDB: {e}")
            return []
    
    def get_session_id(self) -> str:
        """Get the current session ID"""
        return self.session_id


# Global logger instance
_logger_instance: Optional[LoggingService] = None


def initialize_logger(app_name: str = "marvel-champions",
                      verbosity: LogLevel = LogLevel.INFO,
                      log_dir: str = "logs",
                      mongo_connection: Optional[str] = None,
                      mongo_database: str = "marvel_champions",
                      mongo_collection: str = "logs") -> LoggingService:
    """Initialize and return the global logger instance"""
    global _logger_instance
    _logger_instance = LoggingService(
        app_name=app_name,
        verbosity=verbosity,
        log_dir=log_dir,
        mongo_connection=mongo_connection,
        mongo_database=mongo_database,
        mongo_collection=mongo_collection
    )
    return _logger_instance


def get_logger() -> LoggingService:
    """Get the global logger instance (must initialize first)"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = LoggingService()
    return _logger_instance
