from typing import Optional
from pyrogram.types import Message, CallbackQuery
import json

class BaseHandler:
    def __init__(self, bot):
        self.bot = bot
        self.logger = self.bot.logger
        self.db = self.bot.db

    async def log_action(self, action: str, user_id: int, **kwargs):
        """Log handler actions"""
        self.logger.log_event(
            'bot',
            'INFO',
            f"Action: {action}",
            user_id=user_id,
            **kwargs
        )

    async def handle_error(self, error: Exception, context: str, user_id: Optional[int] = None):
        """Handle and log errors"""
        self.logger.log_event(
            'errors',
            'ERROR',
            str(error),
            context=context,
            user_id=user_id
        )
