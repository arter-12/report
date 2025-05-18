import logging
import os
import sys
from datetime import datetime, timezone
import json
from typing import Dict, Any
import colorlog

class QuantumLogger:
    def __init__(self):
        self.setup_loggers()

    def setup_loggers(self):
        """Setup different loggers for various components"""
        # Determine if we're running on Heroku
        self.is_heroku = 'DYNO' in os.environ
        
        # Main bot logger
        self.bot_logger = self._setup_logger('quantum_bot', format_with_color=True)
        self.report_logger = self._setup_logger('quantum_reports')
        self.session_logger = self._setup_logger('quantum_sessions')
        self.error_logger = self._setup_logger('quantum_errors', level=logging.ERROR)
        self.access_logger = self._setup_logger('quantum_access')

    def _setup_logger(
        self,
        name: str,
        level: int = logging.INFO,
        format_with_color: bool = False
    ) -> logging.Logger:
        """Setup individual logger with specified configuration"""
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Always use stdout for Heroku
        if self.is_heroku:
            handler = logging.StreamHandler(sys.stdout)
        else:
            try:
                # Try to create logs directory and use file handler
                os.makedirs('logs', exist_ok=True)
                handler = logging.FileHandler(f'logs/{name}.log')
            except (OSError, IOError):
                # Fallback to stdout if file creation fails
                handler = logging.StreamHandler(sys.stdout)

        if format_with_color and sys.stdout.isatty():
            # Use colored output only if in terminal
            formatter = colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def log_report(self, data: Dict[str, Any]):
        """Log report information"""
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        log_data = {
            "timestamp": timestamp,
            **data
        }
        self.report_logger.info(json.dumps(log_data))

    def log_session(self, action: str, data: Dict[str, Any]):
        """Log session-related actions"""
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        log_data = {
            "timestamp": timestamp,
            "action": action,
            **data
        }
        self.session_logger.info(json.dumps(log_data))

    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context"""
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        log_data = {
            "timestamp": timestamp,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        self.error_logger.error(json.dumps(log_data))

    def log_access(self, user_id: int, action: str, status: str):
        """Log user access and actions"""
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        log_data = {
            "timestamp": timestamp,
            "user_id": user_id,
            "action": action,
            "status": status
        }
        self.access_logger.info(json.dumps(log_data))
