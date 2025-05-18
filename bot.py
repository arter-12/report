from pyrogram import Client, filters, types
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone
import asyncio
import logging
import signal
import sys
import os
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
from utils.logger import QuantumLogger

class QuantumReportBot:
    def __init__(self):
        """Initialize Quantum Report Bot"""
        # Bot information
        self.start_time = datetime.now(timezone.utc)
        self.version = "1.0.0"
        self.creator = "Xepel"
        self.last_updated = "2025-05-18 18:23:18"

        # Environment setup
        self.is_heroku = 'DYNO' in os.environ
        self.data_dir = '/tmp/quantum_bot' if self.is_heroku else 'data'
        os.makedirs(self.data_dir, exist_ok=True)

        # Initialize components
        self.config = Config()
        self.db = Database(db_path=f"{self.data_dir}/quantum.db")
        self.logger = QuantumLogger()

        # Initialize bot client
        self.bot = Client(
            "QuantumReportBot",
            api_id=self.config.api_id,
            api_hash=self.config.api_hash,
            bot_token=self.config.bot_token,
            workdir=f"{self.data_dir}/sessions"
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
        
        self.logger.bot_logger.info(
            f"Bot initialized at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC by {self.creator}"
        )

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
                f"Version: {self.version}\n"
                f"Creator: {self.creator}\n"
                f"Last Updated: {self.last_updated} UTC\n\n"
                f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                f"Uptime: {str(uptime).split('.')[0]}\n"
                f"Active Users: {stats.get('active_users', 0)}\n"
                f"Total Sessions: {stats.get('total_sessions', 0)}\n"
                f"Reports Today: {stats.get('today_reports', 0)}\n"
                f"Success Rate: {stats.get('success_rate', 0):.1f}%\n"
                f"Maintenance Mode: {'🔧 On' if self.maintenance_mode else '✅ Off'}\n"
                f"Environment: {'Heroku' if self.is_heroku else 'Local'}"
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

    async def check_heroku_setup(self):
        """Verify Heroku-specific setup"""
        if self.is_heroku:
            required_vars = ['API_ID', 'API_HASH', 'BOT_TOKEN', 'OWNER_ID']
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            
            if missing_vars:
                self.logger.error_logger.error(
                    f"Missing required environment variables: {', '.join(missing_vars)}"
                )
                raise ValueError(
                    f"Missing required environment variables: {', '.join(missing_vars)}"
                )
            
            # Create temporary directories
            os.makedirs('/tmp/quantum_bot/sessions', exist_ok=True)
            os.makedirs('/tmp/quantum_bot/stats', exist_ok=True)
            
            self.logger.bot_logger.info("Heroku setup verified successfully")

    async def periodic_session_verification(self):
        """Verify sessions periodically"""
        while self.is_running:
            try:
                self.logger.bot_logger.info("Starting periodic session verification")
                await self.session_handler.verify_all_sessions()
            except Exception as e:
                self.logger.error_logger.error(f"Error in session verification: {str(e)}")
            await asyncio.sleep(3600)  # Check every hour

    async def periodic_stats_update(self):
        """Update statistics periodically"""
        while self.is_running:
            try:
                self.logger.bot_logger.info("Updating bot statistics")
                await self.stats_manager.update_bot_stats()
            except Exception as e:
                self.logger.error_logger.error(f"Error updating stats: {str(e)}")
            await asyncio.sleep(300)  # Update every 5 minutes

    async def periodic_backup(self):
        """Create periodic backups"""
        while self.is_running and not self.is_heroku:
            try:
                self.logger.bot_logger.info("Creating database backup")
                await self.db.create_backup()
            except Exception as e:
                self.logger.error_logger.error(f"Error creating backup: {str(e)}")
            await asyncio.sleep(86400)  # Backup daily

    async def start(self):
        """Start the bot"""
        try:
            if self.is_heroku:
                await self.check_heroku_setup()
                
            await self.bot.start()
            self.is_running = True
            self.logger.bot_logger.info("Bot started successfully")
            
            # Start periodic tasks
            asyncio.create_task(self.periodic_session_verification())
            asyncio.create_task(self.periodic_stats_update())
            
            # Don't run backup task on Heroku
            if not self.is_heroku:
                asyncio.create_task(self.periodic_backup())
            
            while self.is_running:
                await asyncio.sleep(1)
        except Exception as e:
            self.logger.error_logger.error(f"Error starting bot: {str(e)}")
            raise
        finally:
            await self.stop()

    async def stop(self):
        """Stop the bot"""
        try:
            self.is_running = False
            await self.session_manager.close_all_clients()
            await self.bot.stop()
            self.logger.bot_logger.info("Bot stopped successfully")
        except Exception as e:
            self.logger.error_logger.error(f"Error stopping bot: {str(e)}")

async def main():
    """Main function to run the bot"""
    bot = QuantumReportBot()
    
    def signal_handler():
        """Handle shutdown signals"""
        bot.logger.bot_logger.info("Shutdown signal received")
        bot.is_running = False
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await bot.start()
    except Exception as e:
        bot.logger.error_logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)
