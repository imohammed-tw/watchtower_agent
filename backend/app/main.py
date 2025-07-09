"""
FastAPI application entry point
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    await db.initialize()
    print("✅ Database initialized")

    yield

    # Shutdown
    print("👋 Shutting down...")


def create_app() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title="AI Watchtower Backend",
        description="Multi-Agent Newsletter Generation System",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8080"],
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

    @app.get("/")
    async def root():
        return {"message": "AI Watchtower Backend", "version": "1.0.0"}

    @app.get("/health")
    async def health():
        return {"status": "healthy", "debug": settings.debug}

    return app


app = create_app()

if __name__ == "__main__":
    print("🚀 Starting AI Watchtower Backend")
    print(f"📡 Server: http://{settings.host}:{settings.port}")
    print(f"📚 Docs: http://{settings.host}:{settings.port}/docs")

    uvicorn.run(
        "app.main:app", host=settings.host, port=settings.port, reload=settings.debug
    )
