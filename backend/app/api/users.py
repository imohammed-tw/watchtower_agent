# File: backend/app/api/users.py - ENHANCED VERSION

"""
User management API endpoints - ENHANCED with debugging
"""

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel

from models import UserPreferences
from database import db

router = APIRouter()

# Enhanced request model for better validation
class UserPreferencesUpdate(BaseModel):
    keywords: List[str] = []
    preferred_sources: List[str] = []
    excluded_sources: List[str] = []
    industry_focus: List[str] = []
    content_types: List[str] = ["regulatory", "technical", "market"]
    urgency_threshold: int = 5
    relevance_threshold: float = 0.7

@router.post("/preferences")
async def save_user_preferences(preferences: UserPreferences):
    """Save user preferences with enhanced debugging"""
    try:
        print(f"💾 Saving preferences for user: {preferences.user_id}")
        print(f"   Keywords: {preferences.keywords}")
        print(f"   Preferred sources: {preferences.preferred_sources}")
        print(f"   Excluded sources: {preferences.excluded_sources}")
        print(f"   Industry focus: {preferences.industry_focus}")
        
        success = await db.save_user_preferences(preferences)
        if success:
            print(f"✅ Successfully saved preferences for user {preferences.user_id}")
            return {
                "status": "success", 
                "message": "Preferences saved",
                "preferences_summary": {
                    "keywords_count": len(preferences.keywords),
                    "preferred_sources_count": len(preferences.preferred_sources),
                    "excluded_sources_count": len(preferences.excluded_sources),
                    "industry_focus_count": len(preferences.industry_focus)
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save preferences")

    except Exception as e:
        print(f"❌ Error saving preferences: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error saving preferences: {str(e)}"
        )


@router.get("/preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """Get user preferences with enhanced debugging"""
    try:
        print(f"📖 Getting preferences for user: {user_id}")
        
        preferences = await db.get_user_preferences(user_id)
        if preferences:
            print(f"✅ Found existing preferences for user {user_id}")
            print(f"   Keywords: {preferences.keywords}")
            print(f"   Preferred sources: {preferences.preferred_sources}")
            return {"preferences": preferences}
        else:
            print(f"⚠️ No existing preferences for user {user_id}, returning defaults")
            # Return default preferences
            default_preferences = UserPreferences(user_id=user_id)
            return {"preferences": default_preferences}

    except Exception as e:
        print(f"❌ Error getting preferences: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting preferences: {str(e)}"
        )


@router.put("/preferences/{user_id}")
async def update_user_preferences(user_id: str, preferences_update: UserPreferencesUpdate):
    """Update user preferences with enhanced validation"""
    try:
        print(f"🔄 Updating preferences for user: {user_id}")
        print(f"   New keywords: {preferences_update.keywords}")
        print(f"   New preferred sources: {preferences_update.preferred_sources}")
        
        # Create full preferences object
        preferences = UserPreferences(
            user_id=user_id,
            keywords=preferences_update.keywords,
            preferred_sources=preferences_update.preferred_sources,
            excluded_sources=preferences_update.excluded_sources,
            industry_focus=preferences_update.industry_focus,
            content_types=preferences_update.content_types,
            urgency_threshold=preferences_update.urgency_threshold,
            relevance_threshold=preferences_update.relevance_threshold
        )

        success = await db.save_user_preferences(preferences)
        if success:
            print(f"✅ Successfully updated preferences for user {user_id}")
            return {
                "status": "success", 
                "message": "Preferences updated",
                "updated_preferences": {
                    "keywords": preferences.keywords,
                    "preferred_sources": preferences.preferred_sources,
                    "excluded_sources": preferences.excluded_sources,
                    "industry_focus": preferences.industry_focus
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update preferences")

    except Exception as e:
        print(f"❌ Error updating preferences: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error updating preferences: {str(e)}"
        )

@router.get("/preferences/{user_id}/debug")
async def debug_user_preferences(user_id: str):
    """Debug endpoint to check what preferences are actually stored"""
    try:
        import aiosqlite
        import json
        from config import settings
        
        db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
        
        async with aiosqlite.connect(db_path) as database:
            cursor = await database.execute(
                "SELECT preferences FROM users WHERE id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                raw_prefs = row[0]
                parsed_prefs = json.loads(raw_prefs)
                
                return {
                    "user_id": user_id,
                    "found_in_database": True,
                    "raw_preferences": raw_prefs,
                    "parsed_preferences": parsed_prefs,
                    "preferred_sources": parsed_prefs.get("preferred_sources", []),
                    "keywords": parsed_prefs.get("keywords", []),
                    "industry_focus": parsed_prefs.get("industry_focus", []),
                    "excluded_sources": parsed_prefs.get("excluded_sources", [])
                }
            else:
                return {
                    "user_id": user_id,
                    "found_in_database": False,
                    "message": "No preferences stored for this user"
                }
                
    except Exception as e:
        return {
            "error": str(e),
            "user_id": user_id
        }

@router.post("/preferences/test")
async def test_preferences_workflow():
    """Test endpoint to verify preferences workflow"""
    test_user_id = "test_preferences_user"
    
    try:
        # Create test preferences
        test_preferences = UserPreferences(
            user_id=test_user_id,
            keywords=["AI governance", "compliance", "security"],
            preferred_sources=["TechCrunch", "MIT Technology Review", "Reuters"],
            excluded_sources=["Random Blog"],
            industry_focus=["Healthcare", "Finance"],
            relevance_threshold=0.7
        )
        
        # Save them
        success = await db.save_user_preferences(test_preferences)
        if not success:
            return {"error": "Failed to save test preferences"}
        
        # Retrieve them
        retrieved = await db.get_user_preferences(test_user_id)
        
        return {
            "test_status": "success",
            "saved_successfully": success,
            "retrieved_successfully": retrieved is not None,
            "preferences_match": (
                retrieved.keywords == test_preferences.keywords and
                retrieved.preferred_sources == test_preferences.preferred_sources
            ) if retrieved else False,
            "original_preferences": {
                "keywords": test_preferences.keywords,
                "preferred_sources": test_preferences.preferred_sources,
                "excluded_sources": test_preferences.excluded_sources
            },
            "retrieved_preferences": {
                "keywords": retrieved.keywords if retrieved else None,
                "preferred_sources": retrieved.preferred_sources if retrieved else None,
                "excluded_sources": retrieved.excluded_sources if retrieved else None
            } if retrieved else None
        }
        
    except Exception as e:
        return {"error": str(e), "test_status": "failed"}