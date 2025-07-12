"""API v1 routes."""

from fastapi import APIRouter
from .auth import router as auth_router
from .api_keys import router as api_keys_router
from .chat import router as chat_router
from .ai_chat import router as ai_chat_router
from .code import router as code_router
from .integrated_chat import router as integrated_chat_router
from .test import router as test_router

api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(api_keys_router)
api_router.include_router(chat_router)
api_router.include_router(ai_chat_router)
api_router.include_router(code_router)
api_router.include_router(integrated_chat_router)
api_router.include_router(test_router)

__all__ = ["api_router"]