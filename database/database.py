# Add these methods to your Database class

async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
    """Get user settings from database"""
    try:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT settings FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            
            if row and row[0]:
                return json.loads(row[0])
            return {
                "language": "en",
                "notifications": True,
                "theme": "light"
            }
    except Exception as e:
        self.logger.error(f"Error getting user settings: {str(e)}")
        return {
            "language": "en",
            "notifications": True,
            "theme": "light"
        }

async def update_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
    """Update user settings in database"""
    try:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET settings = ? WHERE user_id = ?",
                (json.dumps(settings), user_id)
            )
            await db.commit()
            return True
    except Exception as e:
        self.logger.error(f"Error updating user settings: {str(e)}")
        return False
