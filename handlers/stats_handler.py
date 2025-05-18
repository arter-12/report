from .base_handler import BaseHandler
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone
import json
import plotly.graph_objects as go
import io

class StatsHandler(BaseHandler):
    def __init__(self, bot_instance):
        super().__init__(bot_instance)

    async def handle_stats(self, callback_query: CallbackQuery):
        """Handle statistics menu"""
        user_id = callback_query.from_user.id
        
        if await self.check_user_auth(user_id, 'owner'):
            await self._show_owner_stats(callback_query)
        else:
            await self._show_user_stats(callback_query)

    async def _show_owner_stats(self, callback_query: CallbackQuery):
        """Show owner statistics"""
        stats = await self.bot.db.get_bot_stats()
        
        text = (
            "📊 **Bot Statistics**\n\n"
            f"Total Users: {stats['total_users']}\n"
            f"Premium Users: {stats['premium_users']}\n"
            f"Active Sessions: {stats['active_sessions']}\n"
            f"Total Reports: {stats['total_reports']}\n"
            f"Success Rate: {stats['success_rate']:.1f}%\n\n"
            f"Today's Reports: {stats['today_reports']}\n"
            f"Weekly Reports: {stats['weekly_reports']}\n"
            f"Monthly Reports: {stats['monthly_reports']}"
        )

        buttons = [
            [
                InlineKeyboardButton("📈 Detailed Stats", callback_data="stats_detailed"),
                InlineKeyboardButton("👥 User Stats", callback_data="stats_users")
            ],
            [
                InlineKeyboardButton("📊 Generate Graph", callback_data="stats_graph"),
                InlineKeyboardButton("📥 Export Data", callback_data="stats_export")
            ],
            [InlineKeyboardButton("« Back", callback_data="main_menu")]
        ]

        await self.edit_message(
            callback_query.message,
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def _show_user_stats(self, callback_query: CallbackQuery):
        """Show user statistics"""
        user_id = callback_query.from_user.id
        stats = await self.bot.db.get_user_stats(user_id)
        
        text = (
            "📊 **Your Statistics**\n\n"
            f"Active Sessions: {stats['active_sessions']}\n"
            f"Total Reports: {stats['total_reports']}\n"
            f"Successful Reports: {stats['successful_reports']}\n"
            f"Failed Reports: {stats['failed_reports']}\n"
            f"Success Rate: {stats['success_rate']:.1f}%\n\n"
            f"Today's Reports: {stats['today_reports']}\n"
            f"Weekly Reports: {stats['weekly_reports']}"
        )

        buttons = [
            [
                InlineKeyboardButton("📈 Detailed Stats", callback_data="stats_detailed"),
                InlineKeyboardButton("📊 View Graph", callback_data="stats_graph")
            ],
            [InlineKeyboardButton("« Back", callback_data="main_menu")]
        ]

        await self.edit_message(
            callback_query.message,
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def generate_stats_graph(self, user_id: int):
        """Generate statistics graph"""
        stats = await self.bot.db.get_user_report_history(user_id)
        
        dates = [datetime.fromisoformat(s['timestamp']) for s in stats]
        success = [s['success_count'] for s in stats]
        failed = [s['fail_count'] for s in stats]

        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=success,
            name="Successful",
            line=dict(color='green', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=failed,
            name="Failed",
            line=dict(color='red', width=2)
        ))

        fig.update_layout(
            title="Report History",
            xaxis_title="Date",
            yaxis_title="Reports",
            template="plotly_dark"
        )

        img_bytes = fig.to_image(format="png")
        return io.BytesIO(img_bytes)

    async def export_stats(self, user_id: int):
        """Export statistics as JSON"""
        stats = await self.bot.db.get_user_stats(user_id)
        history = await self.bot.db.get_user_report_history(user_id)
        
        export_data = {
            "user_id": user_id,
            "export_date": datetime.now(timezone.utc).isoformat(),
            "stats": stats,
            "history": history
        }

        return json.dumps(export_data, indent=4)
