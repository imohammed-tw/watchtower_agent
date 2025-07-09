"""
User management API endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List

from models import UserPreferences
from database import db

router = APIRouter()


@router.post("/preferences")
async def save_user_preferences(preferences: UserPreferences):
    """Save user preferences"""
    try:
        success = await db.save_user_preferences(preferences)
        if success:
            return {"status": "success", "message": "Preferences saved"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save preferences")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error saving preferences: {str(e)}"
        )


@router.get("/preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """Get user preferences"""
    try:
        preferences = await db.get_user_preferences(user_id)
        if preferences:
            return {"preferences": preferences}
        else:
            # Return default preferences
            default_preferences = UserPreferences(user_id=user_id)
            return {"preferences": default_preferences}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting preferences: {str(e)}"
        )


@router.put("/preferences/{user_id}")
async def update_user_preferences(user_id: str, preferences: UserPreferences):
    """Update user preferences"""
    try:
        # Ensure user_id matches
        preferences.user_id = user_id

        success = await db.save_user_preferences(preferences)
        if success:
            return {"status": "success", "message": "Preferences updated"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update preferences")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating preferences: {str(e)}"
        )
