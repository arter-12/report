from .base_handler import BaseHandler
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone
import json

class SettingsHandler(BaseHandler):
    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        self.available_languages = ['en', 'es', 'ru', 'ar', 'hi', 'zh']
        self.available_themes = ['default', 'dark', 'light', 'blue']

    async def handle_settings(self, callback_query: CallbackQuery):
        """Handle settings menu"""
        user_id = callback_query.from_user.id
        user_settings = await self.bot.db.get_user_settings(user_id)
        
        if await self.check_user_auth(user_id, 'owner'):
            await self._show_owner_settings(callback_query)
        else:
            await self._show_user_settings(callback_query, user_settings)

    async def _show_owner_settings(self, callback_query: CallbackQuery):
        """Show owner settings menu"""
        buttons = [
            [
                InlineKeyboardButton("👥 User Management", callback_data="settings_users"),
                InlineKeyboardButton("🤖 Bot Settings", callback_data="settings_bot")
            ],
            [
                InlineKeyboardButton("🔒 Security", callback_data="settings_security"),
                InlineKeyboardButton("📊 Analytics", callback_data="settings_analytics")
            ],
            [
                InlineKeyboardButton("💾 Backup", callback_data="settings_backup"),
                InlineKeyboardButton("🔄 Auto-Report", callback_data="settings_auto_report")
            ],
            [
                InlineKeyboardButton("🌐 Language", callback_data="settings_language"),
                InlineKeyboardButton("🎨 Theme", callback_data="settings_theme")
            ],
            [InlineKeyboardButton("« Back", callback_data="main_menu")]
        ]

        await self.edit_message(
            callback_query.message,
            "⚙️ **Owner Settings Panel**\n\n"
            "Manage all aspects of your bot:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def _show_user_settings(self, callback_query: CallbackQuery, settings: dict):
        """Show user settings menu"""
        buttons = [
            [
                InlineKeyboardButton("🌐 Language", callback_data="settings_language"),
                InlineKeyboardButton("🎨 Theme", callback_data="settings_theme")
            ],
            [
                InlineKeyboardButton("🔔 Notifications", callback_data="settings_notifications"),
                InlineKeyboardButton("⚡️ Report Mode", callback_data="settings_report_mode")
            ],
            [InlineKeyboardButton("« Back", callback_data="main_menu")]
        ]

        text = (
            "⚙️ **User Settings**\n\n"
            f"🌐 Language: {settings['language']}\n"
            f"🎨 Theme: {settings['theme']}\n"
            f"🔔 Notifications: {'On' if settings['notifications'] else 'Off'}\n"
            f"⚡️ Report Mode: {settings['report_mode']}"
        )

        await self.edit_message(
            callback_query.message,
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def handle_language_setting(self, callback_query: CallbackQuery):
        """Handle language selection"""
        buttons = []
        row = []
        
        for i, lang in enumerate(self.available_languages, 1):
            row.append(InlineKeyboardButton(
                f"🌐 {lang.upper()}", 
                callback_data=f"set_lang_{lang}"
            ))
            
            if i % 2 == 0 or i == len(self.available_languages):
                buttons.append(row)
                row = []
        
        buttons.append([InlineKeyboardButton("« Back", callback_data="settings")])
        
        await self.edit_message(
            callback_query.message,
            "🌐 **Select Language**\n\n"
            "Choose your preferred language:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def handle_theme_setting(self, callback_query: CallbackQuery):
        """Handle theme selection"""
        buttons = []
        for theme in self.available_themes:
            buttons.append([InlineKeyboardButton(
                f"🎨 {theme.title()}", 
                callback_data=f"set_theme_{theme}"
            )])
        
        buttons.append([InlineKeyboardButton("« Back", callback_data="settings")])
        
        await self.edit_message(
            callback_query.message,
            "🎨 **Select Theme**\n\n"
            "Choose your preferred theme:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def handle_security_settings(self, callback_query: CallbackQuery):
        """Handle security settings (owner only)"""
        if not await self.check_user_auth(callback_query.from_user.id, 'owner'):
            await self.answer_callback(
                callback_query,
                "⚠️ Owner access required!",
                show_alert=True
            )
            return

        security_settings = self.bot.config.get_security_settings()
        
        buttons = [
            [
                InlineKeyboardButton(
                    "🔒 2FA", 
                    callback_data="security_2fa"
                ),
                InlineKeyboardButton(
                    "🚫 Anti-Flood", 
                    callback_data="security_antiflood"
                )
            ],
            [
                InlineKeyboardButton(
                    "👥 Access Control", 
                    callback_data="security_access"
                ),
                InlineKeyboardButton(
                    "📝 Logs", 
                    callback_data="security_logs"
                )
            ],
            [InlineKeyboardButton("« Back", callback_data="settings")]
        ]

        text = (
            "🔒 **Security Settings**\n\n"
            f"2FA: {'Enabled' if security_settings['2fa'] else 'Disabled'}\n"
            f"Anti-Flood: {'Enabled' if security_settings['antiflood'] else 'Disabled'}\n"
            f"Max Sessions: {security_settings['max_sessions']}\n"
            f"Session Timeout: {security_settings['session_timeout']}s"
        )

        await self.edit_message(
            callback_query.message,
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
