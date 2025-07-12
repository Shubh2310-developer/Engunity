"""Test endpoints without authentication."""

from fastapi import APIRouter
from ...services.groq_service import create_groq_completion

router = APIRouter()


@router.get("/test/health")
async def test_health():
    """Simple health check."""
    return {"status": "ok", "message": "Test endpoint working"}


@router.post("/test/ai")
async def test_ai_simple(message: str = "Hello"):
    """Test AI without authentication."""
    try:
        messages = [{"role": "user", "content": message}]
        
        response = await create_groq_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        
        return {
            "status": "success",
            "response": response
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }