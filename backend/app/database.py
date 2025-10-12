import asyncio
import aiosqlite
import json
import os
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import settings
from models import UserPreferences, Newsletter, WorkflowState


class Database:
    """Simple database operations - Windows compatible"""

    def __init__(self):
        self.db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Enable WAL mode for better concurrency
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA synchronous=NORMAL")
            await db.execute("PRAGMA busy_timeout=30000")
            
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
                    format TEXT,
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

            # Ensure older DBs get the 'format' column
            try:
                await db.execute("ALTER TABLE newsletters ADD COLUMN format TEXT")
            except Exception:
                pass

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
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("PRAGMA busy_timeout=30000")
                    
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
                await db.execute("PRAGMA busy_timeout=30000")
                
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
        """Save newsletter with Windows-compatible locking"""
        async with self._lock:
            max_retries = 5
            base_delay = 0.5
            
            for attempt in range(max_retries):
                try:
                    # Generate unique ID with microseconds for uniqueness
                    timestamp = datetime.utcnow()
                    newsletter_id = f"{newsletter.user_id}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
                    
                    print(f"💾 Saving newsletter (attempt {attempt + 1}/{max_retries}): {newsletter_id}")
                    
                    async with aiosqlite.connect(self.db_path) as db:
                        await db.execute("PRAGMA busy_timeout=30000")
                        await db.execute("PRAGMA journal_mode=WAL")
                        await db.execute("PRAGMA synchronous=NORMAL")
                        
                        # Use BEGIN IMMEDIATE to get exclusive lock
                        await db.execute("BEGIN IMMEDIATE")
                        
                        try:
                            await db.execute(
                                    """
                                    INSERT INTO newsletters 
                                    (id, user_id, format, title, content, config, sections, total_articles, generated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                    (
                                        newsletter_id,
                                        newsletter.user_id,
                                    newsletter.config.format.value,
                                        newsletter.title,
                                        newsletter.content,
                                        newsletter.config.model_dump_json(),
                                        json.dumps(newsletter.sections),
                                        newsletter.total_articles,
                                        newsletter.generated_at.isoformat(),
                                    ),
                                )
                            await db.commit()
                            print(f"✅ Newsletter saved successfully: {newsletter_id}")
                            return True
                                
                        except Exception as e:
                            await db.rollback()
                            raise e
                            
                except Exception as e:
                    print(f"❌ Error saving newsletter (attempt {attempt + 1}/{max_retries}): {e}")
                    
                    if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        delay = base_delay * (2 ** attempt) + (time.time() % 0.1)
                        print(f"⏳ Database locked, retrying in {delay:.2f} seconds...")
                        await asyncio.sleep(delay)
                        continue
                    elif attempt == max_retries - 1:
                        print(f"❌ Final attempt failed: {e}")
                        return False
                    else:
                        print(f"❌ Non-lock error: {e}")
                        return False
            
            return False

    async def get_user_newsletters(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user's recent newsletters"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA busy_timeout=30000")
                
                cursor = await db.execute(
                    """
                    SELECT id, title, generated_at, total_articles, COALESCE(format, '') as format
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
                        "format": row[4] if row[4] else None,
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"Error getting newsletters: {e}")
            return []


# Global database instance
db = Database()