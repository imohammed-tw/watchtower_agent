"""
FastAPI application entry point - UPDATED with Dashboard API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
from config import settings
from database import db
from api.newsletter import router as newsletter_router
from api.users import router as users_router
from api.export import router as export_router
from api.dashboard import router as dashboard_router  # NEW: Dashboard API
from api.auth import router as auth_router  # NEW: Authentication API

import os
import atexit

def cleanup_database_files():
    """Clean up database lock files"""
    db_path = "./ai_watchtower.db"
    lock_files = [
        db_path + "-wal", 
        db_path + "-shm",
        db_path + "-journal"
    ]
    
    for lock_file in lock_files:
        if os.path.exists(lock_file):
            try:
                if os.path.getsize(lock_file) == 0:
                    os.remove(lock_file)
                    print(f"🔧 Removed stale lock file: {lock_file}")
            except Exception as e:
                print(f"⚠️ Could not remove {lock_file}: {e}")

# Register cleanup and run on startup
atexit.register(cleanup_database_files)
cleanup_database_files()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    await db.initialize()
    print("✅ Database initialized")
    
    # Initialize orchestrator and alert system
    from agents.orchestrator import orchestrator
    try:
        await orchestrator.initialize()
        print("✅ Orchestrator and alert system initialized")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize orchestrator: {e}")

    yield

    # Shutdown
    print("👋 Shutting down...")


def create_app() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title="AI Watchtower Backend",
        description="Multi-Agent Newsletter Generation System with Risk Assessment",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware - Updated for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # React dev server
            "http://localhost:8080",  # Alternative dev server
            "http://localhost:5173",  # Vite dev server
            "https://preview-rai-watchtower-ui-design-kzmqp31vamdrgp29ozlz.vusercontent.net"  # Your UI preview
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(
        newsletter_router, prefix="/api/v1/newsletter", tags=["Newsletter"]
    )
    app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(export_router, prefix="/api/v1/export", tags=["Export"])
    
    # NEW: Include dashboard router for frontend metrics and alerts
    app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])
    
    # NEW: Include auth router for authentication
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

    @app.get("/")
    async def root():
        return {
            "message": "AI Watchtower Backend", 
            "version": "1.0.0",
            "features": [
                "Multi-agent newsletter generation",
                "Risk assessment and alerts",
                "Dashboard metrics API",
                "Export functionality",
                "User preference management"
            ]
        }

    @app.get("/health")
    async def health():
        """Enhanced health check with component status"""
        try:
            # Test database
            newsletters = await db.get_user_newsletters("health_check", limit=1)
            db_status = "healthy"
        except Exception:
            db_status = "error"
        
        # Test orchestrator
        from agents.orchestrator import orchestrator
        try:
            agent_status = orchestrator.get_agents_status()
            orchestrator_status = "healthy"
        except Exception:
            orchestrator_status = "error"
            agent_status = {}
        
        return {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "debug": settings.debug,
            "components": {
                "database": db_status,
                "orchestrator": orchestrator_status,
                "agents": agent_status
            },
            "version": "1.0.0",
            "timestamp": settings.get_utc_time().isoformat()
        }

    return app


app = create_app()

if __name__ == "__main__":
    print("🚀 Starting AI Watchtower Backend")
    print(f"📡 Server: http://{settings.host}:{settings.port}")
    print(f"📚 Docs: http://{settings.host}:{settings.port}/docs")
    print(f"🎯 Dashboard API: http://{settings.host}:{settings.port}/api/v1/dashboard")
    print(f"📊 Newsletter API: http://{settings.host}:{settings.port}/api/v1/newsletter")

    uvicorn.run(
        "app.main:app", host=settings.host, port=settings.port, reload=settings.debug
    )