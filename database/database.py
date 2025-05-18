import aiosqlite
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union
import logging
import os
import sys

class Database:
    def __init__(self, db_path: str = "data/quantum.db"):
        self.db_path = db_path
        self.logger = self._setup_logger()
        asyncio.create_task(self._initialize_db())

    def _setup_logger(self) -> logging.Logger:
        """Setup logger with fallback to stdout for Heroku"""
        logger = logging.getLogger('Database')
        logger.setLevel(logging.INFO)
        
        # Check if we're running on Heroku
        if 'DYNO' in os.environ:
            # Use stdout for Heroku
            handler = logging.StreamHandler(sys.stdout)
        else:
            # Try to use file, fallback to stdout if not possible
            try:
                os.makedirs('logs', exist_ok=True)
                handler = logging.FileHandler('logs/database.log')
            except (OSError, IOError):
                handler = logging.StreamHandler(sys.stdout)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    async def _initialize_db(self):
        """Initialize database tables"""
        try:
            # Ensure the data directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.executescript("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        language TEXT DEFAULT 'en',
                        joined_date TEXT,
                        is_premium BOOLEAN DEFAULT FALSE,
                        settings TEXT,
                        stats TEXT
                    );

                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        session_string TEXT,
                        phone_number TEXT,
                        first_name TEXT,
                        added_date TEXT,
                        last_used TEXT,
                        last_verified TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        stats TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    );

                    CREATE TABLE IF NOT EXISTS reports (
                        report_id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        target_type TEXT,
                        target_id TEXT,
                        reason TEXT,
                        timestamp TEXT,
                        sessions_used TEXT,
                        success_count INTEGER DEFAULT 0,
                        fail_count INTEGER DEFAULT 0,
                        status TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    );

                    CREATE TABLE IF NOT EXISTS logs (
                        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        user_id INTEGER,
                        action TEXT,
                        data TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    );
                """)
                await db.commit()
                self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            raise
