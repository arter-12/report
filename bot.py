from pyrogram import Client, filters, types
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone
import asyncio
import logging
import signal
import sys
from typing import Dict, Any, Optional
import json

from config.config import Config
from database.database import Database
from handlers.base_handler import BaseHandler
from handlers.report_handler import ReportHandler
from handlers.session_handler import SessionHandler
from handlers.settings_handler import SettingsHandler
from handlers.stats_handler import StatsHandler
from utils.helpers import SessionManager, StatsManager
from utils.decorators import error_handler, log_action

class QuantumReportBot:
    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
        self.config = Config()
        self.db = Database()
        self.setup_logging()
        
        # Initialize bot client
        self.bot = Client(
            "QuantumReportBot",
            api_id=self.config.api_id,
            api_hash=self.config.api_hash,
            bot_token=self.config.bot_token
        )

        # Initialize managers
        self.session_manager = SessionManager(self.db, self.config)
        self.stats_manager = StatsManager(self.db)
        
        # Initialize handlers
        self.report_handler = ReportHandler(self)
        self.session_handler = SessionHandler(self)
        self.settings_handler = SettingsHandler(self)
        self.stats_handler = StatsHandler(self)
        
        # Bot state
        self.is_running = False
        self.maintenance_mode = False
        self.user_state = {}
        
        # Setup handlers
        self.setup_handlers()
        
        self.logger.info(f"Bot initialized at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    def setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger('QuantumBot')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler('logs/bot.log')
        file_handler.setLevel(logging.INFO)
        
        # Error handler
        error_handler = logging.FileHandler('logs/errors.log')
        error_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)

    def setup_handlers(self):
        """Setup message and callback handlers"""
        
        @self.bot.on_message(filters.command("start"))
        @error_handler
        @log_action("start")
        async def start_command(client: Client, message: Message):
            """Handle /start command"""
            await self.session_handler.handle_start(message)

        @self.bot.on_message(filters.command("help"))
        @error_handler
        async def help_command(client: Client, message: Message):
            """Handle /help command"""
            user_id = message.from_user.id
            lang = await self.db.get_user_language(user_id)
            
            help_text = (
                "🔰 **Quantum Report Bot Help**\n\n"
                "Available commands:\n"
                "/start - Start the bot\n"
                "/help - Show this help message\n"
                "/status - Show bot status\n"
                "/settings - Configure settings\n"
                "/cancel - Cancel current operation\n\n"
                "Use the buttons below for main features:"
            )
            
            buttons = [
                [
                    InlineKeyboardButton("📱 Sessions", callback_data="sessions"),
                    InlineKeyboardButton("🎯 Report", callback_data="report")
                ],
                [
                    InlineKeyboardButton("📊 Stats", callback_data="stats"),
                    InlineKeyboardButton("⚙️ Settings", callback_data="settings")
                ]
            ]
            
            await message.reply_text(
                help_text,
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        @self.bot.on_message(filters.command("status"))
        @error_handler
        async def status_command(client: Client, message: Message):
            """Handle /status command"""
            uptime = datetime.now(timezone.utc) - self.start_time
            stats = await self.db.get_bot_stats()
            
            status_text = (
                "🤖 **Bot Status**\n\n"
                f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                f"Uptime: {str(uptime).split('.')[0]}\n"
                f"Active Users: {stats['active_users']}\n"
                f"Total Sessions: {stats['total_sessions']}\n"
                f"Reports Today: {stats['today_reports']}\n"
                f"Success Rate: {stats['success_rate']:.1f}%\n"
                f"Maintenance Mode: {'🔧 On' if self.maintenance_mode else '✅ Off'}"
            )
            
            await message.reply_text(status_text)

        @self.bot.on_callback_query()
        @error_handler
        async def handle_callback(client: Client, callback_query: CallbackQuery):
            """Handle callback queries"""
            data = callback_query.data
            user_id = callback_query.from_user.id
            
            # Map callbacks to handlers
            handlers = {
                'sessions': self.session_handler.handle_sessions,
                'report': self.report_handler.handle_report,
                'stats': self.stats_handler.handle_stats,
                'settings': self.settings_handler.handle_settings
            }
            
            if data in handlers:
                await handlers[data](callback_query)
            else:
                # Handle specific callbacks
                if data.startswith('add_session'):
                    await self.session_handler.handle_add_session(callback_query)
                elif data.startswith('delete_session'):
                    await self.session_handler.handle_delete_session(callback_query)
                elif data.startswith('verify_session'):
                    await self.session_handler.handle_verify_session(callback_query)
                elif data.startswith('report_'):
                    await self.report_handler.handle_specific_report(callback_query)
                elif data.startswith('settings_'):
                    await self.settings_handler.handle_specific_setting(callback_query)
                elif data.startswith('stats_'):
                    await self.stats_handler.handle_specific_stat(callback_query)

        @self.bot.on_message(filters.private & filters.text)
        @error_handler
        async def handle_message(client: Client, message: Message):
            """Handle text messages"""
            user_id = message.from_user.id
            
            if user_id in self.user_state:
                state = self.user_state[user_id]
                
                if state.get('waiting_for') == 'session':
                    await self.session_handler.process_session_string(message)
                elif state.get('waiting_for') == 'target':
                    await self.report_handler.process_target(message)
                elif state.get('waiting_for') == 'confirmation':
                    await self.report_handler.process_confirmation(message)
                else:
                    await message.reply_text(
                        "❌ Invalid state. Please use the menu buttons."
                    )
            else:
                await message.reply_text(
                    "Please use the menu buttons to interact with the bot."
                )

    async def start(self):
        """Start the bot"""
        try:
            await self.bot.start()
            self.is_running = True
            self.logger.info("Bot started successfully")
            
            # Start periodic tasks
            asyncio.create_task(self.periodic_session_verification())
            asyncio.create_task(self.periodic_stats_update())
            asyncio.create_task(self.periodic_backup())
            
            while self.is_running:
                await asyncio.sleep(1)
        except Exception as e:
            self.logger.error(f"Error starting bot: {str(e)}")
            raise
        finally:
            await self.stop()

    async def stop(self):
        """Stop the bot"""
        try:
            self.is_running = False
            await self.session_manager.close_all_clients()
            await self.bot.stop()
            self.logger.info("Bot stopped successfully")
        except Exception as e:
            self.logger.error(f"Error stopping bot: {str(e)}")

    async def periodic_session_verification(self):
        """Verify sessions periodically"""
        while self.is_running:
            try:
                self.logger.info("Starting periodic session verification")
                await self.session_handler.verify_all_sessions()
            except Exception as e:
                self.logger.error(f"Error in session verification: {str(e)}")
            await asyncio.sleep(3600)  # Check every hour

    async def periodic_stats_update(self):
        """Update statistics periodically"""
        while self.is_running:
            try:
                self.logger.info("Updating bot statistics")
                await self.stats_manager.update_bot_stats()
            except Exception as e:
                self.logger.error(f"Error updating stats: {str(e)}")
            await asyncio.sleep(300)  # Update every 5 minutes

    async def periodic_backup(self):
        """Create periodic backups"""
        while self.is_running:
            try:
                self.logger.info("Creating database backup")
                await self.db.create_backup()
            except Exception as e:
                self.logger.error(f"Error creating backup: {str(e)}")
            await asyncio.sleep(86400)  # Backup daily

async def main():
    """Main function to run the bot"""
    bot = QuantumReportBot()
    
    def signal_handler():
        """Handle shutdown signals"""
        bot.logger.info("Shutdown signal received")
        bot.is_running = False
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await bot.start()
    except Exception as e:
        bot.logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)
