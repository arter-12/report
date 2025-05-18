import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime, timezone
import json
from typing import Dict, Any
import colorlog

class QuantumLogger:
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = logs_dir
        self.ensure_log_directory()
        self.setup_loggers()

    def ensure_log_directory(self):
        """Create log directories if they don't exist"""
        directories = [
            self.logs_dir,
            f"{self.logs_dir}/reports",
            f"{self.logs_dir}/sessions",
            f"{self.logs_dir}/errors",
            f"{self.logs_dir}/access"
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def setup_loggers(self):
        """Setup different loggers for various components"""
        # Main bot logger
        self.bot_logger = self._setup_logger(
            'quantum_bot',
            f'{self.logs_dir}/bot.log',
            format_with_color=True
        )

        # Report logger
        self.report_logger = self._setup_logger(
            'quantum_reports',
            f'{self.logs_dir}/reports/reports.log'
        )

        # Session logger
        self.session_logger = self._setup_logger(
            'quantum_sessions',
            f'{self.logs_dir}/sessions/sessions.log'
        )

        # Error logger
        self.error_logger = self._setup_logger(
            'quantum_errors',
            f'{self.logs_dir}/errors/errors.log',
            level=logging.ERROR
        )

        # Access logger
        self.access_logger = self._setup_logger(
            'quantum_access',
            f'{self.logs_dir}/access/access.log'
        )

    def _setup_logger(
        self,
        name: str,
        log_file: str,
        level: int = logging.INFO,
        format_with_color: bool = False
    ) -> logging.Logger:
        """Setup individual logger with specified configuration"""
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # File handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)

        # Console handler with optional color
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        if format_with_color:
            # Colored formatter for console
            color_formatter = colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
            console_handler.setFormatter(color_formatter)
        else:
            # Standard formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)

        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

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
