from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone
import asyncio

class SessionHandler:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.verification_lock = asyncio.Lock()

    async def handle_add_session(self, callback_query: CallbackQuery):
        """Handle adding new session"""
        user_id = callback_query.from_user.id
        
        # Check session limit
        current_sessions = len(self.bot.db.get_user_sessions(user_id))
        max_sessions = float('inf') if user_id == self.bot.config.owner_id else 50
        
        if current_sessions >= max_sessions:
            await callback_query.answer(
                "You've reached the maximum session limit!",
                show_alert=True
            )
            return

        self.bot.user_state[user_id] = {"state": "waiting_for_session"}
        
        await callback_query.edit_message_text(
            "📱 **Add New Session**\n\n"
            "1️⃣ Visit: https://my.telegram.org\n"
            "2️⃣ Login and get API ID & Hash\n"
            "3️⃣ Use session generator: @StringFatherBot\n"
            "4️⃣ Send the session string here\n\n"
            "Current Sessions: {current_sessions}/{max_sessions}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back", callback_data="sessions")
            ]])
        )

    async def handle_delete_session(self, callback_query: CallbackQuery):
        """Handle session deletion"""
        user_id = callback_query.from_user.id
        sessions = self.bot.db.get_user_sessions(user_id)
        
        if not sessions:
            await callback_query.answer("No sessions to delete!", show_alert=True)
            return

        # Create buttons for each session
        buttons = []
        for i, session in enumerate(sessions, 1):
            client_info = await self.get_client_info(session['session'])
            buttons.append([
                InlineKeyboardButton(
                    f"{i}. {client_info['name']} (+{client_info['phone']})",
                    callback_data=f"delete_session_{i}"
                )
            ])
        
        buttons.append([InlineKeyboardButton("« Back", callback_data="sessions")])
        
        await callback_query.edit_message_text(
            "🗑 **Delete Session**\n\n"
            "Select the session you want to delete:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def handle_verify_sessions(self, callback_query: CallbackQuery):
        """Handle session verification"""
        async with self.verification_lock:
            user_id = callback_query.from_user.id
            sessions = self.bot.db.get_user_sessions(user_id)
            
            if not sessions:
                await callback_query.answer("No sessions to verify!", show_alert=True)
                return

            status_msg = await callback_query.edit_message_text(
                "🔄 **Verifying Sessions...**\n\n"
                "This may take a few moments."
            )

            results = {
                "total": len(sessions),
                "valid": 0,
                "invalid": 0
            }

            for i, session in enumerate(sessions[:], 1):
                try:
                    client = await self.bot.get_client(session['session'])
                    await client.start()
                    await client.stop()
                    results["valid"] += 1
                    session["verified"] = True
                except Exception:
                    results["invalid"] += 1
                    sessions.remove(session)
                
                await status_msg.edit_text(
                    f"🔄 **Verifying Sessions...**\n\n"
                    f"Progress: {i}/{results['total']}\n"
                    f"Valid: {results['valid']}\n"
                    f"Invalid: {results['invalid']}"
                )
                await asyncio.sleep(1)

            self.bot.db.update_user_sessions(user_id, sessions)
            
            await status_msg.edit_text(
                "✅ **Session Verification Complete**\n\n"
                f"Total Sessions: {results['total']}\n"
                f"Valid Sessions: {results['valid']}\n"
                f"Invalid Sessions: {results['invalid']}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Back", callback_data="sessions")
                ]])
            )
