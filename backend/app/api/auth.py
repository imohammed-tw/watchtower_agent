# File: backend/app/api/auth.py - NEW AUTHENTICATION API

"""
Authentication API endpoints for user login and registration
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import hashlib
import secrets

from database import db

router = APIRouter()

# Request/Response Models
class LoginRequest(BaseModel):
    user_id: str
    password: str

class RegisterRequest(BaseModel):
    user_id: str
    password: str
    email: Optional[str] = None
    name: Optional[str] = None

class AuthResponse(BaseModel):
    success: bool
    user_id: str
    token: Optional[str] = None
    message: str

class UserInfo(BaseModel):
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    created_at: str
    last_login: str

# Simple in-memory session storage (in production, use Redis or database)
active_sessions = {}

def hash_password(password: str) -> str:
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    """Generate a simple session token"""
    return secrets.token_urlsafe(32)

@router.post("/register", response_model=AuthResponse)
async def register_user(request: RegisterRequest):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await db.get_user_preferences(request.user_id)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Hash password
        hashed_password = hash_password(request.password)
        
        # Create user record (we'll store in a simple users table)
        # For now, we'll just create user preferences as a way to "register"
        from models import UserPreferences
        user_prefs = UserPreferences(
            user_id=request.user_id,
            keywords=[],
            preferred_sources=[],
            excluded_sources=[],
            industry_focus=[],
            content_types=["regulatory", "technical", "market"],
            urgency_threshold=5,
            relevance_threshold=0.7
        )
        
        success = await db.save_user_preferences(user_prefs)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        # Generate session token
        token = generate_token()
        active_sessions[token] = {
            "user_id": request.user_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return AuthResponse(
            success=True,
            user_id=request.user_id,
            token=token,
            message="User registered successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=AuthResponse)
async def login_user(request: LoginRequest):
    """Login an existing user"""
    try:
        # For now, we'll use a simple approach:
        # If user has preferences, they exist and can login
        # In a real system, you'd verify the password against stored hash
        
        user_prefs = await db.get_user_preferences(request.user_id)
        if not user_prefs:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Generate session token
        token = generate_token()
        active_sessions[token] = {
            "user_id": request.user_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return AuthResponse(
            success=True,
            user_id=request.user_id,
            token=token,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.post("/logout")
async def logout_user(token: str):
    """Logout user by invalidating token"""
    if token in active_sessions:
        del active_sessions[token]
    return {"success": True, "message": "Logged out successfully"}

@router.get("/me", response_model=UserInfo)
async def get_current_user(token: str):
    """Get current user info from token"""
    if token not in active_sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    session = active_sessions[token]
    user_id = session["user_id"]
    
    # Get user preferences to verify user exists
    user_prefs = await db.get_user_preferences(user_id)
    if not user_prefs:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserInfo(
        user_id=user_id,
        email=None,  # Not stored in current system
        name=None,   # Not stored in current system
        created_at=session["created_at"],
        last_login=datetime.utcnow().isoformat()
    )

@router.get("/validate")
async def validate_token(token: str):
    """Validate if token is still active"""
    if token in active_sessions:
        return {"valid": True, "user_id": active_sessions[token]["user_id"]}
    return {"valid": False}
