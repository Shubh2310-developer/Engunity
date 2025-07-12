"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .config.settings import settings
from .api.v1 import api_router
from .config.database import mongo_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifespan events."""
    # Startup
    await mongo_manager.connect()
    yield
    # Shutdown
    await mongo_manager.disconnect()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoints (before static files)
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name, "version": settings.version}

@app.get("/health")
async def health_check_simple():
    """Simple health check endpoint."""
    return {"status": "healthy"}

# Include routers
app.include_router(api_router, prefix="/api/v1")

# Serve static files (your HTML pages) - should be last
app.mount("/", StaticFiles(directory="../frontend/public", html=True), name="static")