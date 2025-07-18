"""Main FastAPI application."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.exception_handlers import http_exception_handler
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

# Custom exception handler for authentication
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions, especially 401 Unauthorized for document endpoints."""
    # If it's a 401 error on document endpoints, redirect to login
    if exc.status_code == 401 and request.url.path.startswith('/api/v1/documents'):
        # Check if request accepts HTML (browser request vs API request)
        accept_header = request.headers.get('accept', '')
        if 'text/html' in accept_header:
            return RedirectResponse(url='/login.html', status_code=302)
    
    # For all other cases, use default handler
    return await http_exception_handler(request, exc)

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
import os
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/public"))
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")