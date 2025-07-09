"""API v1 routes."""

from fastapi import APIRouter
from .auth import router as auth_router
from .api_keys import router as api_keys_router

api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(api_keys_router)

__all__ = ["api_router"]