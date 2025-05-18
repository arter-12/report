from .base_handler import BaseHandler
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional, Dict, Any
import json

class SettingsHandler(BaseHandler):
    def __init__(self, bot):
        super().__init__(bot)
        self.settings_cache = {}

    async def handle_settings(self, callback_query: CallbackQuery):
        """Handle settings menu"""
        try:
            user_id = callback_query.from_user.id
            await self.log_action("settings_menu", user_id)

            settings = await self.get_user_settings(user_id)
            buttons = self.create_settings_buttons(settings)

            await callback_query.message.edit_text(
                "⚙️ **Settings**\n\n"
                "Configure your preferences below:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception as e:
            await self.handle_error(e, "handle_settings", user_id)
            await callback_query.answer(
                "❌ Error accessing settings. Please try again.",
                show_alert=True
            )

    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings from database"""
        try:
            if user_id in self.settings_cache:
                return self.settings_cache[user_id]

            settings = await self.db.get_user_settings(user_id)
            self.settings_cache[user_id] = settings
            return settings
        except Exception as e:
            await self.handle_error(e, "get_user_settings", user_id)
            return {}

    def create_settings_buttons(self, settings: Dict[str, Any]) -> list:
        """Create settings menu buttons"""
        buttons = [
            [
                InlineKeyboardButton(
                    f"🌐 Language: {settings.get('language', 'en')}",
                    callback_data="settings_language"
                )
            ],
            [
                InlineKeyboardButton(
                    f"🔔 Notifications: {'On' if settings.get('notifications', True) else 'Off'}",
                    callback_data="settings_notifications"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="main_menu"
                )
            ]
        ]
        return buttons

    async def handle_specific_setting(self, callback_query: CallbackQuery):
        """Handle specific setting updates"""
        try:
            user_id = callback_query.from_user.id
            data = callback_query.data.split('_')[1]

            if data == "language":
                await self.show_language_settings(callback_query)
            elif data == "notifications":
                await self.toggle_notifications(callback_query)
            else:
                await callback_query.answer("Invalid setting option")

        except Exception as e:
            await self.handle_error(e, "handle_specific_setting", user_id)
            await callback_query.answer(
                "❌ Error updating setting. Please try again.",
                show_alert=True
            )

    async def show_language_settings(self, callback_query: CallbackQuery):
        """Show language selection menu"""
        buttons = [
            [
                InlineKeyboardButton("English 🇬🇧", callback_data="setlang_en"),
                InlineKeyboardButton("Español 🇪🇸", callback_data="setlang_es")
            ],
            [
                InlineKeyboardButton("Русский 🇷🇺", callback_data="setlang_ru"),
                InlineKeyboardButton("中文 🇨🇳", callback_data="setlang_zh")
            ],
            [
                InlineKeyboardButton("हिंदी 🇮🇳", callback_data="setlang_hi"),
                InlineKeyboardButton("العربية 🇸🇦", callback_data="setlang_ar")
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="settings")
            ]
        ]
        await callback_query.message.edit_text(
            "🌐 **Select your language**\n\n"
            "Choose your preferred language from the options below:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def toggle_notifications(self, callback_query: CallbackQuery):
        """Toggle notification settings"""
        try:
            user_id = callback_query.from_user.id
            settings = await self.get_user_settings(user_id)
            
            # Toggle notification setting
            current = settings.get('notifications', True)
            settings['notifications'] = not current
            
            # Update database
            await self.db.update_user_settings(user_id, settings)
            
            # Update cache
            self.settings_cache[user_id] = settings
            
            # Update message
            buttons = self.create_settings_buttons(settings)
            await callback_query.message.edit_reply_markup(
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            
            await callback_query.answer(
                f"Notifications turned {'on' if not current else 'off'}",
                show_alert=True
            )

        except Exception as e:
            await self.handle_error(e, "toggle_notifications", user_id)
            await callback_query.answer(
                "❌ Error updating notifications. Please try again.",
                show_alert=True
            )
