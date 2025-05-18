import aiosqlite
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union
import logging

class Database:
    def __init__(self, db_path: str = "data/quantum.db"):
        self.db_path = db_path
        self.logger = self._setup_logger()
        asyncio.create_task(self._initialize_db())

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('Database')
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler('logs/database.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        logger.addHandler(handler)
        return logger

    async def _initialize_db(self):
        """Initialize database tables"""
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

    async def add_user(self, user_id: int, **kwargs) -> bool:
        """Add new user to database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, language, joined_date, is_premium, settings, stats)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    kwargs.get('username'),
                    kwargs.get('first_name'),
                    kwargs.get('language', 'en'),
                    kwargs.get('joined_date', datetime.now(timezone.utc).isoformat()),
                    kwargs.get('is_premium', False),
                    json.dumps(kwargs.get('settings', {})),
                    json.dumps(kwargs.get('stats', {
                        'total_reports': 0,
                        'successful_reports': 0,
                        'failed_reports': 0,
                        'last_report': None
                    }))
                ))
                await db.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error adding user: {str(e)}")
            return False

    async def add_session(self, user_id: int, session_string: str, **kwargs) -> bool:
        """Add new session"""
        try:
            session_id = f"session_{user_id}_{datetime.now(timezone.utc).timestamp()}"
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO sessions 
                    (session_id, user_id, session_string, phone_number, first_name, 
                     added_date, last_used, last_verified, is_active, stats)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    user_id,
                    session_string,
                    kwargs.get('phone_number'),
                    kwargs.get('first_name'),
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat(),
                    True,
                    json.dumps({
                        'reports_count': 0,
                        'success_count': 0,
                        'fail_count': 0
                    })
                ))
                await db.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error adding session: {str(e)}")
            return False

    async def add_report(self, user_id: int, **kwargs) -> bool:
        """Add new report"""
        try:
            report_id = f"report_{user_id}_{datetime.now(timezone.utc).timestamp()}"
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO reports 
                    (report_id, user_id, target_type, target_id, reason, 
                     timestamp, sessions_used, success_count, fail_count, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report_id,
                    user_id,
                    kwargs.get('target_type'),
                    kwargs.get('target_id'),
                    kwargs.get('reason'),
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(kwargs.get('sessions_used', [])),
                    kwargs.get('success_count', 0),
                    kwargs.get('fail_count', 0),
                    kwargs.get('status', 'pending')
                ))
                await db.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error adding report: {str(e)}")
            return False

    async def get_user_sessions(self, user_id: int) -> List[Dict]:
        """Get all active sessions for user"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT * FROM sessions 
                    WHERE user_id = ? AND is_active = TRUE 
                    ORDER BY added_date DESC
                """, (user_id,))
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting sessions: {str(e)}")
            return []

    async def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT stats FROM users WHERE user_id = ?
                """, (user_id,))
                row = await cursor.fetchone()
                return json.loads(row['stats']) if row else {}
        except Exception as e:
            self.logger.error(f"Error getting stats: {str(e)}")
            return {}

    async def update_user_settings(self, user_id: int, settings: Dict) -> bool:
        """Update user settings"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE users SET settings = ? WHERE user_id = ?
                """, (json.dumps(settings), user_id))
                await db.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error updating settings: {str(e)}")
            return False
