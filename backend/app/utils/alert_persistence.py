# File: backend/app/utils/alert_persistence.py - FIXED SQL SYNTAX

"""
Alert Persistence and Database Integration - FIXED VERSION
Handles storing, retrieving, and managing alerts in the database
"""

import asyncio
import aiosqlite
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from config import settings
from utils.risk_assessment import RiskAlert, RiskLevel, AlertType


class AlertDatabase:
    """
    Database operations for alert management
    
    WHAT THIS DOES:
    1. Stores alerts in database for persistence
    2. Tracks alert completion status
    3. Provides alert retrieval and filtering
    4. Manages alert lifecycle (creation, completion, cleanup)
    """
    
    def __init__(self):
        self.db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize alerts table in database - FIXED SQL SYNTAX"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA busy_timeout=30000")
            
            # Create alerts table - FIXED: Removed INDEX from CREATE TABLE
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    title TEXT,
                    description TEXT,
                    risk_level TEXT,
                    alert_type TEXT,
                    deadline TEXT,
                    action_required TEXT,
                    source_article_id TEXT,
                    created_at TEXT,
                    completed BOOLEAN DEFAULT FALSE,
                    completed_at TEXT,
                    completed_by TEXT,
                    completion_note TEXT
                )
            """
            )
            
            # FIXED: Create indexes separately after table creation
            try:
                await db.execute("CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts(user_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_alerts_risk_level ON alerts(risk_level)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_alerts_completed ON alerts(completed)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at)")
            except Exception as e:
                print(f"⚠️ Warning: Could not create indexes: {e}")
            
            # Create dashboard metrics table for caching
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS dashboard_metrics (
                    user_id TEXT PRIMARY KEY,
                    total_articles INTEGER DEFAULT 0,
                    sections INTEGER DEFAULT 5,
                    high_risk_items INTEGER DEFAULT 0,
                    actions_required INTEGER DEFAULT 0,
                    risk_level TEXT DEFAULT 'low',
                    impact_score INTEGER DEFAULT 0,
                    last_updated TEXT,
                    newsletter_date TEXT
                )
            """
            )
            
            await db.commit()
            print("✅ Alert database tables initialized")

    async def save_alert(self, alert: RiskAlert, user_id: str) -> bool:
        """Save alert to database"""
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("PRAGMA busy_timeout=30000")
                    
                    await db.execute(
                        """
                        INSERT OR REPLACE INTO alerts 
                        (id, user_id, title, description, risk_level, alert_type, 
                         deadline, action_required, source_article_id, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            alert.id,
                            user_id,
                            alert.title,
                            alert.description,
                            alert.risk_level.value,
                            alert.alert_type.value,
                            alert.deadline.isoformat() if alert.deadline else None,
                            alert.action_required,
                            alert.source_article_id,
                            alert.created_at.isoformat()
                        ),
                    )
                    await db.commit()
                    
                    print(f"💾 Saved alert: {alert.id} for user {user_id}")
                    return True
                    
            except Exception as e:
                print(f"❌ Error saving alert: {e}")
                return False

    async def get_user_alerts(
        self, 
        user_id: str, 
        include_completed: bool = False,
        risk_levels: Optional[List[str]] = None,
        alert_types: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get alerts for a user with filtering options"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA busy_timeout=30000")
                
                # Build query conditions
                conditions = ["user_id = ?"]
                params = [user_id]
                
                if not include_completed:
                    conditions.append("completed = FALSE")
                
                if risk_levels:
                    placeholders = ",".join("?" * len(risk_levels))
                    conditions.append(f"risk_level IN ({placeholders})")
                    params.extend(risk_levels)
                
                if alert_types:
                    placeholders = ",".join("?" * len(alert_types))
                    conditions.append(f"alert_type IN ({placeholders})")
                    params.extend(alert_types)
                
                where_clause = " AND ".join(conditions)
                
                cursor = await db.execute(
                    f"""
                    SELECT id, title, description, risk_level, alert_type, 
                           deadline, action_required, created_at, completed,
                           completed_at, completed_by, completion_note
                    FROM alerts 
                    WHERE {where_clause}
                    ORDER BY 
                        CASE risk_level 
                            WHEN 'critical' THEN 4
                            WHEN 'high' THEN 3  
                            WHEN 'medium' THEN 2
                            WHEN 'low' THEN 1
                            ELSE 0
                        END DESC,
                        created_at DESC
                    LIMIT ?
                    """,
                    params + [limit]
                )
                
                rows = await cursor.fetchall()
                
                alerts = []
                for row in rows:
                    alert_data = {
                        "id": row[0],
                        "title": row[1],
                        "description": row[2],
                        "risk_level": row[3],
                        "alert_type": row[4],
                        "deadline": row[5],
                        "action_required": row[6],
                        "created_at": row[7],
                        "completed": bool(row[8]),
                        "completed_at": row[9],
                        "completed_by": row[10],
                        "completion_note": row[11]
                    }
                    alerts.append(alert_data)
                
                print(f"📊 Retrieved {len(alerts)} alerts for user {user_id}")
                return alerts
                
        except Exception as e:
            print(f"❌ Error getting user alerts: {e}")
            return []

    async def complete_alert(
        self, 
        alert_id: str, 
        completed_by: str, 
        completion_note: Optional[str] = None
    ) -> bool:
        """Mark alert as completed"""
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("PRAGMA busy_timeout=30000")
                    
                    completion_time = datetime.utcnow().isoformat()
                    
                    cursor = await db.execute(
                        """
                        UPDATE alerts 
                        SET completed = TRUE, completed_at = ?, completed_by = ?, completion_note = ?
                        WHERE id = ?
                    """,
                        (completion_time, completed_by, completion_note, alert_id)
                    )
                    
                    await db.commit()
                    
                    if cursor.rowcount > 0:
                        print(f"✅ Alert {alert_id} marked as completed by {completed_by}")
                        return True
                    else:
                        print(f"⚠️ Alert {alert_id} not found for completion")
                        return False
                        
            except Exception as e:
                print(f"❌ Error completing alert: {e}")
                return False

    async def get_alert_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get alert metrics for dashboard"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA busy_timeout=30000")
                
                # Get active alerts breakdown
                cursor = await db.execute(
                    """
                    SELECT risk_level, alert_type, COUNT(*) 
                    FROM alerts 
                    WHERE user_id = ? AND completed = FALSE 
                    GROUP BY risk_level, alert_type
                    """,
                    (user_id,)
                )
                
                rows = await cursor.fetchall()
                
                # Initialize counters
                by_risk = {"critical": 0, "high": 0, "medium": 0, "low": 0}
                by_type = {
                    "compliance_deadline": 0,
                    "security_threat": 0, 
                    "regulatory_change": 0,
                    "market_disruption": 0
                }
                
                # Count alerts by category
                for risk_level, alert_type, count in rows:
                    by_risk[risk_level] = by_risk.get(risk_level, 0) + count
                    by_type[alert_type] = by_type.get(alert_type, 0) + count
                
                total_alerts = sum(by_risk.values())
                high_risk_items = by_risk["critical"] + by_risk["high"]
                
                return {
                    "total_alerts": total_alerts,
                    "high_risk_items": high_risk_items,
                    "actions_required": total_alerts,  # All active alerts require action
                    "by_risk_level": by_risk,
                    "by_type": by_type,
                    "compliance_deadlines": by_type["compliance_deadline"],
                    "security_threats": by_type["security_threat"]
                }
                
        except Exception as e:
            print(f"❌ Error getting alert metrics: {e}")
            return {
                "total_alerts": 0,
                "high_risk_items": 0,
                "actions_required": 0,
                "by_risk_level": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "by_type": {"compliance_deadline": 0, "security_threat": 0, "regulatory_change": 0, "market_disruption": 0}
            }

    async def update_dashboard_metrics(
        self, 
        user_id: str, 
        metrics: Dict[str, Any]
    ) -> bool:
        """Update cached dashboard metrics"""
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("PRAGMA busy_timeout=30000")
                    
                    last_updated = datetime.utcnow().isoformat()
                    
                    await db.execute(
                        """
                        INSERT OR REPLACE INTO dashboard_metrics 
                        (user_id, total_articles, sections, high_risk_items, 
                         actions_required, risk_level, impact_score, last_updated, newsletter_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            user_id,
                            metrics.get("total_articles", 0),
                            metrics.get("sections", 5),
                            metrics.get("high_risk_items", 0),
                            metrics.get("actions_required", 0),
                            metrics.get("risk_level", "low"),
                            metrics.get("impact_score", 0),
                            last_updated,
                            metrics.get("newsletter_date")
                        )
                    )
                    
                    await db.commit()
                    print(f"💾 Updated dashboard metrics for user {user_id}")
                    return True
                    
            except Exception as e:
                print(f"❌ Error updating dashboard metrics: {e}")
                return False

    async def get_cached_dashboard_metrics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached dashboard metrics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA busy_timeout=30000")
                
                cursor = await db.execute(
                    """
                    SELECT total_articles, sections, high_risk_items, actions_required,
                           risk_level, impact_score, last_updated, newsletter_date
                    FROM dashboard_metrics
                    WHERE user_id = ?
                    """,
                    (user_id,)
                )
                
                row = await cursor.fetchone()
                if row:
                    return {
                        "total_articles": row[0],
                        "sections": row[1],
                        "high_risk_items": row[2],
                        "actions_required": row[3],
                        "risk_level": row[4],
                        "impact_score": row[5],
                        "last_updated": row[6],
                        "newsletter_date": row[7]
                    }
                
                return None
                
        except Exception as e:
            print(f"❌ Error getting cached metrics: {e}")
            return None

    async def cleanup_old_alerts(self, days_old: int = 90) -> int:
        """Clean up old completed alerts"""
        async with self._lock:
            try:
                cutoff_date = (datetime.utcnow() - timedelta(days=days_old)).isoformat()
                
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("PRAGMA busy_timeout=30000")
                    
                    cursor = await db.execute(
                        """
                        DELETE FROM alerts 
                        WHERE completed = TRUE AND completed_at < ?
                        """,
                        (cutoff_date,)
                    )
                    
                    await db.commit()
                    deleted_count = cursor.rowcount
                    
                    if deleted_count > 0:
                        print(f"🧹 Cleaned up {deleted_count} old completed alerts")
                    
                    return deleted_count
                    
            except Exception as e:
                print(f"❌ Error cleaning up alerts: {e}")
                return 0

    async def get_alert_statistics(self) -> Dict[str, Any]:
        """Get system-wide alert statistics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA busy_timeout=30000")
                
                # Total alerts
                cursor = await db.execute("SELECT COUNT(*) FROM alerts")
                total_alerts = (await cursor.fetchone())[0]
                
                # Active alerts
                cursor = await db.execute("SELECT COUNT(*) FROM alerts WHERE completed = FALSE")
                active_alerts = (await cursor.fetchone())[0]
                
                # Completion rate
                cursor = await db.execute("SELECT COUNT(*) FROM alerts WHERE completed = TRUE")
                completed_alerts = (await cursor.fetchone())[0]
                
                completion_rate = (completed_alerts / total_alerts * 100) if total_alerts > 0 else 0
                
                return {
                    "total_alerts": total_alerts,
                    "active_alerts": active_alerts,
                    "completed_alerts": completed_alerts,
                    "completion_rate": round(completion_rate, 1),
                    "last_calculated": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            print(f"❌ Error getting alert statistics: {e}")
            return {"error": str(e)}


# Global alert database instance
alert_db = AlertDatabase()