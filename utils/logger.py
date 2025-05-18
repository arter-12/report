import logging
import os
import sys
from datetime import datetime, timezone
import json
from typing import Dict, Any
import colorlog

class QuantumLogger:
    def __init__(self):
        """Initialize logger system"""
        self.is_heroku = 'DYNO' in os.environ
        self.loggers = {}
        self.setup_loggers()

    def setup_loggers(self):
        """Setup all required loggers"""
        logger_names = [
            'bot', 'reports', 'sessions', 'errors', 
            'access', 'settings', 'stats'
        ]
        
        for name in logger_names:
            self.loggers[name] = self._setup_logger(name)

    def _setup_logger(self, name: str) -> logging.Logger:
        """Setup individual logger"""
        logger = logging.getLogger(f'quantum_{name}')
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers = []
        
        # Always use StreamHandler for Heroku
        handler = logging.StreamHandler(sys.stdout)
        
        # Use colored formatter for console
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s[%(asctime)s][%(name)s] %(levelname)s: %(message)s",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

    def get_logger(self, name: str) -> logging.Logger:
        """Get logger by name"""
        return self.loggers.get(name, self.loggers['bot'])

    def log_event(self, logger_name: str, level: str, message: str, **kwargs):
        """Log an event with additional data"""
        logger = self.get_logger(logger_name)
        log_data = {
            "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            "message": message,
            **kwargs
        }
        
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(json.dumps(log_data))
