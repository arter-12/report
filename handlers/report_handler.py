from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone
import asyncio

class ReportHandler:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.report_queue = asyncio.Queue()
        self.is_reporting = False

    async def handle_report(self, callback_query: CallbackQuery):
        """Handle report button click"""
        user_id = callback_query.from_user.id
        sessions = self.bot.db.get_user_sessions(user_id)
        
        if not sessions:
            await callback_query.edit_message_text(
                "❌ **No Active Sessions**\n\n"
                "You need at least one active session to report content.\n"
                "Add a session first!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("➕ Add Session", callback_data="add_session"),
                    InlineKeyboardButton("« Back", callback_data="main_menu")
                ]])
            )
            return

        await callback_query.edit_message_text(
            "🎯 **Mass Report System**\n\n"
            f"Active Sessions: {len(sessions)}\n\n"
            "Select what you want to report:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📢 Channel", callback_data="report_channel"),
                    InlineKeyboardButton("👥 Group", callback_data="report_group")
                ],
                [
                    InlineKeyboardButton("👤 User", callback_data="report_user"),
                    InlineKeyboardButton("💭 Message", callback_data="report_message")
                ],
                [
                    InlineKeyboardButton("📊 Report History", callback_data="report_history"),
                    InlineKeyboardButton("⚙️ Report Settings", callback_data="report_settings")
                ],
                [InlineKeyboardButton("« Back", callback_data="main_menu")]
            ])
        )

    async def process_report(self, target_type: str, target_id: str, reason: str, sessions: list):
        """Process mass report"""
        total = len(sessions)
        success = 0
        failed = 0
        
        for session in sessions:
            try:
                client = await self.bot.get_client(session['session'])
                await client.start()
                
                if target_type == "channel":
                    await client.report_chat(target_id, reason)
                elif target_type == "message":
                    chat_id, message_id = target_id.split('/')
                    await client.report_chat(chat_id, [int(message_id)], reason)
                
                success += 1
                await client.stop()
            except Exception as e:
                failed += 1
                print(f"Report failed: {str(e)}")
            
            await asyncio.sleep(2)  # Avoid flood wait

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": (success / total) * 100 if total > 0 else 0
        }
