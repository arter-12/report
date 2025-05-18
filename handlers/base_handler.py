from pyrogram import Client
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Union, Dict, Any
from datetime import datetime, timezone
import logging

class BaseHandler:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup handler-specific logger"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        
        # File handler
        fh = logging.FileHandler(f'logs/{self.__class__.__name__.lower()}.log')
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: InlineKeyboardMarkup = None,
        **kwargs
    ) -> Message:
        """Send message with error handling and logging"""
        try:
            return await self.bot.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                **kwargs
            )
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            raise

    async def edit_message(
        self,
        message: Message,
        text: str,
        reply_markup: InlineKeyboardMarkup = None,
        **kwargs
    ) -> Message:
        """Edit message with error handling and logging"""
        try:
            return await message.edit_text(
                text=text,
                reply_markup=reply_markup,
                **kwargs
            )
        except Exception as e:
            self.logger.error(f"Error editing message: {str(e)}")
            raise

    async def answer_callback(
        self,
        callback_query: CallbackQuery,
        text: str = None,
        show_alert: bool = False,
        **kwargs
    ):
        """Answer callback query with error handling"""
        try:
            await callback_query.answer(
                text=text,
                show_alert=show_alert,
                **kwargs
            )
        except Exception as e:
            self.logger.error(f"Error answering callback: {str(e)}")
            raise

    async def get_user_language(self, user_id: int) -> str:
        """Get user's preferred language"""
        try:
            return self.bot.db.get_user_language(user_id)
        except Exception:
            return 'en'  # Default to English

    def get_text(self, key: str, lang: str = 'en', **kwargs) -> str:
        """Get localized text with placeholders"""
        try:
            text = self.bot.messages.get_text(key, lang)
            return text.format(**kwargs) if kwargs else text
        except Exception as e:
            self.logger.error(f"Error getting text: {str(e)}")
            return key

    async def check_user_auth(
        self,
        user_id: int,
        feature: str = None
    ) -> bool:
        """Check user authorization"""
        try:
            if user_id == self.bot.config.owner_id:
                return True
            
            if user_id in self.bot.config.authorized_users:
                if not feature:
                    return True
                    
                user_permissions = self.bot.db.get_user_permissions(user_id)
                return feature in user_permissions
                
            return False
        except Exception as e:
            self.logger.error(f"Error checking auth: {str(e)}")
            return False

    async def log_action(
        self,
        action: str,
        user_id: int,
        data: Dict[str, Any] = None
    ):
        """Log user actions"""
        try:
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "user_id": user_id,
                "data": data or {}
            }
            await self.bot.db.add_log(log_entry)
            self.logger.info(f"Action logged: {action} by user {user_id}")
        except Exception as e:
            self.logger.error(f"Error logging action: {str(e)}")
