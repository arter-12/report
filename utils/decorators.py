from functools import wraps
from typing import Callable, Any
import asyncio
from datetime import datetime, timezone
import logging
from pyrogram.types import Message, CallbackQuery

def rate_limit(limit: int = 2, window: int = 60):
    """
    Rate limiting decorator
    :param limit: Number of allowed calls in the time window
    :param window: Time window in seconds
    """
    def decorator(func: Callable) -> Callable:
        calls = {}
        
        @wraps(func)
        async def wrapper(self, update: Union[Message, CallbackQuery], *args, **kwargs):
            user_id = update.from_user.id
            current_time = datetime.now(timezone.utc).timestamp()
            
            # Initialize or clean old calls
            if user_id not in calls:
                calls[user_id] = []
            calls[user_id] = [t for t in calls[user_id] if current_time - t < window]
            
            # Check rate limit
            if len(calls[user_id]) >= limit:
                wait_time = window - (current_time - calls[user_id][0])
                await update.answer(
                    f"Please wait {int(wait_time)} seconds before trying again.",
                    show_alert=True
                )
                return
            
            # Add current call
            calls[user_id].append(current_time)
            return await func(self, update, *args, **kwargs)
            
        return wrapper
    return decorator

def require_premium(func: Callable) -> Callable:
    """Decorator to check if user has premium access"""
    @wraps(func)
    async def wrapper(self, update: Union[Message, CallbackQuery], *args, **kwargs):
        user_id = update.from_user.id
        
        if not await self.bot.db.is_premium_user(user_id):
            await update.answer(
                "⭐️ This feature requires premium access!\n"
                "Contact the owner to upgrade.",
                show_alert=True
            )
            return
        
        return await func(self, update, *args, **kwargs)
    return wrapper

def owner_only(func: Callable) -> Callable:
    """Decorator for owner-only functions"""
    @wraps(func)
    async def wrapper(self, update: Union[Message, CallbackQuery], *args, **kwargs):
        user_id = update.from_user.id
        
        if user_id != self.bot.config.owner_id:
            await update.answer(
                "🔒 This feature is only available to the bot owner!",
                show_alert=True
            )
            return
        
        return await func(self, update, *args, **kwargs)
    return wrapper

def log_action(action: str):
    """Decorator to log user actions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, update: Union[Message, CallbackQuery], *args, **kwargs):
            user_id = update.from_user.id
            username = update.from_user.username
            
            # Log action start
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "username": username,
                "action": action,
                "status": "started"
            }
            await self.bot.db.add_log(log_entry)
            
            try:
                result = await func(self, update, *args, **kwargs)
                
                # Log action success
                log_entry.update({
                    "status": "success",
                    "completed_at": datetime.now(timezone.utc).isoformat()
                })
                await self.bot.db.add_log(log_entry)
                
                return result
            except Exception as e:
                # Log action failure
                log_entry.update({
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.now(timezone.utc).isoformat()
                })
                await self.bot.db.add_log(log_entry)
                raise
                
        return wrapper
    return decorator

def error_handler(func: Callable) -> Callable:
    """Decorator to handle errors gracefully"""
    @wraps(func)
    async def wrapper(self, update: Union[Message, CallbackQuery], *args, **kwargs):
        try:
            return await func(self, update, *args, **kwargs)
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            logging.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            
            if isinstance(update, CallbackQuery):
                await update.answer(error_msg, show_alert=True)
            else:
                await update.reply_text(error_msg)
            
            # Log error to database
            await self.bot.db.add_error_log({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": update.from_user.id,
                "function": func.__name__,
                "error": str(e),
                "traceback": logging.format_exc()
            })
            
    return wrapper

def require_session(func: Callable) -> Callable:
    """Decorator to check if user has active sessions"""
    @wraps(func)
    async def wrapper(self, update: Union[Message, CallbackQuery], *args, **kwargs):
        user_id = update.from_user.id
        sessions = await self.bot.db.get_user_sessions(user_id)
        
        if not sessions:
            await update.answer(
                "❌ You need at least one active session to use this feature!\n"
                "Add a session first.",
                show_alert=True
            )
            return
        
        return await func(self, update, *args, **kwargs)
    return wrapper

def cooldown(seconds: int = 60):
    """Decorator to add cooldown between function calls"""
    def decorator(func: Callable) -> Callable:
        last_call = {}
        
        @wraps(func)
        async def wrapper(self, update: Union[Message, CallbackQuery], *args, **kwargs):
            user_id = update.from_user.id
            current_time = datetime.now(timezone.utc).timestamp()
            
            if user_id in last_call:
                time_passed = current_time - last_call[user_id]
                if time_passed < seconds:
                    wait_time = int(seconds - time_passed)
                    await update.answer(
                        f"⏳ Please wait {wait_time} seconds before trying again.",
                        show_alert=True
                    )
                    return
            
            last_call[user_id] = current_time
            return await func(self, update, *args, **kwargs)
            
        return wrapper
    return decorator

def maintenance_mode(func: Callable) -> Callable:
    """Decorator to check if bot is in maintenance mode"""
    @wraps(func)
    async def wrapper(self, update: Union[Message, CallbackQuery], *args, **kwargs):
        if self.bot.maintenance_mode and update.from_user.id != self.bot.config.owner_id:
            await update.answer(
                "🛠 Bot is currently under maintenance.\n"
                "Please try again later.",
                show_alert=True
            )
            return
        
        return await func(self, update, *args, **kwargs)
    return wrapper

def track_usage(category: str):
    """Decorator to track feature usage"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, update: Union[Message, CallbackQuery], *args, **kwargs):
            user_id = update.from_user.id
            
            # Track usage start
            usage_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "category": category,
                "feature": func.__name__,
                "status": "started"
            }
            await self.bot.db.add_usage_stat(usage_data)
            
            try:
                result = await func(self, update, *args, **kwargs)
                
                # Track usage success
                usage_data.update({
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat()
                })
                await self.bot.db.add_usage_stat(usage_data)
                
                return result
            except Exception as e:
                # Track usage failure
                usage_data.update({
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.now(timezone.utc).isoformat()
                })
                await self.bot.db.add_usage_stat(usage_data)
                raise
                
        return wrapper
    return decorator
