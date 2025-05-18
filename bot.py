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
import platform

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

# Constants
CURRENT_UTC = "2025-05-18 18:29:45"
CURRENT_USER = "Xepel"

class QuantumReportBot:
    def __init__(self):
        """Initialize Quantum Report Bot"""
        # Bot information
        self.start_time = datetime.now(timezone.utc)
        self.version = "1.0.0"
        self.creator = CURRENT_USER
        self.last_updated = CURRENT_UTC

        # Environment setup
        self.is_heroku = 'DYNO' in os.environ
        self.data_dir = '/tmp/quantum_bot' if self.is_heroku else 'data'
        os.makedirs(self.data_dir, exist_ok=True)

        # Initialize components
        self.config = Config()
        self.db = Database(db_path=f"{self.data_dir}/quantum.db")
        self.logger = QuantumLogger()
        
        # Set event loop policy for Windows
        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        # Initialize bot client with appropriate settings
        self.bot = Client(
            "QuantumReportBot",
            api_id=self.config.api_id,
            api_hash=self.config.api_hash,
            bot_token=self.config.bot_token,
            workdir=f"{self.data_dir}/sessions",
            in_memory=True if self.is_heroku else False
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
        
        # Tasks container
        self.tasks = []

        # Setup handlers
        self.setup_handlers()
        
        self.logger.bot_logger.info(
            f"Bot initialized at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC by {self.creator}"
        )

    # ... (previous handler setup code remains the same)

    async def start(self):
        """Start the bot"""
        try:
            if self.is_heroku:
                await self.check_heroku_setup()
            
            # Start the bot
            await self.bot.start()
            self.is_running = True
            self.logger.bot_logger.info("Bot started successfully")
            
            # Create tasks
            self.tasks = [
                asyncio.create_task(self.periodic_session_verification()),
                asyncio.create_task(self.periodic_stats_update())
            ]
            
            if not self.is_heroku:
                self.tasks.append(asyncio.create_task(self.periodic_backup()))
            
            # Wait for tasks or shutdown
            try:
                await asyncio.gather(*self.tasks)
            except asyncio.CancelledError:
                pass

        except Exception as e:
            self.logger.error_logger.error(f"Error starting bot: {str(e)}")
            raise
        finally:
            await self.stop()

    async def stop(self):
        """Stop the bot gracefully"""
        self.is_running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close session manager and bot
        try:
            await self.session_manager.close_all_clients()
            await self.bot.stop()
            self.logger.bot_logger.info("Bot stopped successfully")
        except Exception as e:
            self.logger.error_logger.error(f"Error stopping bot: {str(e)}")

def run_bot():
    """Run the bot with proper event loop handling"""
    bot = None
    try:
        # Create new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create bot instance
        bot = QuantumReportBot()
        
        # Handle shutdown signals
        def signal_handler():
            if bot and bot.is_running:
                bot.logger.bot_logger.info("Shutdown signal received")
                bot.is_running = False
                # Schedule bot stop in the event loop
                loop.create_task(bot.stop())
        
        # Setup signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
        
        # Run the bot
        loop.run_until_complete(bot.start())
        
    except Exception as e:
        if bot:
            bot.logger.error_logger.error(f"Fatal error: {str(e)}")
        else:
            print(f"Fatal error before bot initialization: {str(e)}")
        sys.exit(1)
    finally:
        try:
            # Clean up tasks
            pending = asyncio.all_tasks(loop)
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
            # Close the loop
            loop.close()
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    # Set debug options for asyncio if needed
    if os.getenv('DEBUG'):
        os.environ['PYTHONASYNCIODEBUG'] = '1'
    
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)
