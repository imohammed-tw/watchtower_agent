"""
Simple database operations using SQLite
"""

import aiosqlite
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import settings
from models import UserPreferences, Newsletter, WorkflowState


class Database:
    """Simple database operations"""

    def __init__(self):
        self.db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")

    async def initialize(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    preferences TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """
            )

            # Newsletters table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS newsletters (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    title TEXT,
                    content TEXT,
                    config TEXT,
                    sections TEXT,
                    total_articles INTEGER,
                    generated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            # Workflows table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    status TEXT,
                    config TEXT,
                    error TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """
            )

            await db.commit()

    async def save_user_preferences(self, preferences: UserPreferences) -> bool:
        """Save user preferences"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                now = datetime.utcnow().isoformat()
                await db.execute(
                    """
                    INSERT OR REPLACE INTO users (id, preferences, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """,
                    (preferences.user_id, preferences.model_dump_json(), now, now),
                )
                await db.commit()
                return True
        except Exception as e:
            print(f"Error saving user preferences: {e}")
            return False

    async def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT preferences FROM users WHERE id = ?", (user_id,)
                )
                row = await cursor.fetchone()
                if row:
                    return UserPreferences.model_validate_json(row[0])
                return None
        except Exception as e:
            print(f"Error getting user preferences: {e}")
            return None

    async def save_newsletter(self, newsletter: Newsletter) -> bool:
        """Save newsletter"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                newsletter_id = (
                    f"{newsletter.user_id}_{newsletter.generated_at.isoformat()}"
                )
                await db.execute(
                    """
                    INSERT INTO newsletters 
                    (id, user_id, title, content, config, sections, total_articles, generated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        newsletter_id,
                        newsletter.user_id,
                        newsletter.title,
                        newsletter.content,
                        newsletter.config.model_dump_json(),
                        json.dumps(newsletter.sections),
                        newsletter.total_articles,
                        newsletter.generated_at.isoformat(),
                    ),
                )
                await db.commit()
                return True
        except Exception as e:
            print(f"Error saving newsletter: {e}")
            return False

    async def get_user_newsletters(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user's recent newsletters"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT id, title, generated_at, total_articles
                    FROM newsletters 
                    WHERE user_id = ?
                    ORDER BY generated_at DESC
                    LIMIT ?
                """,
                    (user_id, limit),
                )

                rows = await cursor.fetchall()
                return [
                    {
                        "id": row[0],
                        "title": row[1],
                        "generated_at": row[2],
                        "total_articles": row[3],
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"Error getting newsletters: {e}")
            return []


# Global database instance
db = Database()
