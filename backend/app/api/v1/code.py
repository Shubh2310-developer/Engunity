"""Code generation API endpoints using Groq llama-3.3-70b-versatile model."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.responses import StreamingResponse
import json

from ...services.auth_service import SupabaseAuthService
from ...services.code_service import CodeGenerationService
from ...db.repositories.mongo_repository import get_repository_manager, RepositoryManager
from ...models.mongo_models import CodeSnippet
from pydantic import BaseModel, Field

router = APIRouter()
security = HTTPBearer()
auth_service = SupabaseAuthService()
code_service = CodeGenerationService()


class CodeGenerationRequest(BaseModel):
    """Request schema for code generation."""
    prompt: str = Field(..., description="Code generation prompt")
    language: str = Field(default="python", description="Programming language")
    framework: Optional[str] = Field(default=None, description="Framework or library")
    complexity: str = Field(default="intermediate", description="Code complexity level")
    include_comments: bool = Field(default=True, description="Include code comments")
    include_tests: bool = Field(default=False, description="Include unit tests")
    max_tokens: int = Field(default=2048, ge=1, le=8192, description="Maximum tokens to generate")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="Sampling temperature")
    save_code: bool = Field(default=True, description="Save generated code to database")


class CodeReviewRequest(BaseModel):
    """Request schema for code review."""
    code: str = Field(..., description="Code to review")
    language: str = Field(..., description="Programming language")
    focus_areas: List[str] = Field(default=["security", "performance", "readability"], description="Review focus areas")
    severity_level: str = Field(default="all", description="Minimum severity level to report")


class CodeOptimizationRequest(BaseModel):
    """Request schema for code optimization."""
    code: str = Field(..., description="Code to optimize")
    language: str = Field(..., description="Programming language")
    optimization_goals: List[str] = Field(default=["performance"], description="Optimization goals")
    preserve_functionality: bool = Field(default=True, description="Preserve original functionality")


class CodeExplanationRequest(BaseModel):
    """Request schema for code explanation."""
    code: str = Field(..., description="Code to explain")
    language: str = Field(..., description="Programming language")
    detail_level: str = Field(default="intermediate", description="Explanation detail level")
    include_examples: bool = Field(default=True, description="Include usage examples")


class CodeResponse(BaseModel):
    """Response schema for code operations."""
    id: str
    code: str
    language: str
    explanation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    tokens_used: Optional[int] = None


async def get_current_user(token: str = Depends(security)):
    """Get current user from token."""
    user = await auth_service.get_user_by_token(token.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user


@router.post("/code/generate", response_model=CodeResponse)
async def generate_code(
    request: CodeGenerationRequest,
    current_user=Depends(get_current_user),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Generate code using AI."""
    try:
        # Generate code using the service
        result = await code_service.generate_code(
            prompt=request.prompt,
            language=request.language,
            framework=request.framework,
            complexity=request.complexity,
            include_comments=request.include_comments,
            include_tests=request.include_tests,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Save to database if requested
        code_id = None
        if request.save_code:
            try:
                code_snippet = CodeSnippet(
                    code=result["code"],
                    language=request.language,
                    description=request.prompt,
                    metadata={
                        "framework": request.framework,
                        "complexity": request.complexity,
                        "include_comments": request.include_comments,
                        "include_tests": request.include_tests,
                        "tokens_used": result.get("tokens_used", 0)
                    }
                )
                
                # Get user ID from Supabase user object
                user_id = current_user.get("id") or current_user.get("sub") or str(current_user.get("email", "unknown"))
                
                code_id = await repo_manager.code_repo.save_code_snippet(
                    user_id=user_id,
                    code_snippet=code_snippet
                )
                
                # Update user stats
                await repo_manager.stats_repo.increment_stats(
                    user_id, 
                    "total_codes"
                )
            except Exception as save_error:
                # Log the save error but don't fail the entire request
                print(f"Warning: Failed to save code snippet: {save_error}")
                # Continue without saving
        
        return CodeResponse(
            id=code_id or f"temp_{result.get('id', 'unknown')}",
            code=result["code"],
            language=request.language,
            explanation=result.get("explanation"),
            metadata=result.get("metadata"),
            created_at=result.get("created_at", ""),
            tokens_used=result.get("tokens_used")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = f"Code generation failed: {str(e)}"
        print(f"Code generation error: {error_details}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_details
        )



@router.post("/code/review")
async def review_code(
    request: CodeReviewRequest,
    current_user=Depends(get_current_user)
):
    """Review code for issues and improvements."""
    try:
        result = await code_service.review_code(
            code=request.code,
            language=request.language,
            focus_areas=request.focus_areas,
            severity_level=request.severity_level
        )
        
        return {
            "review_id": result.get("id"),
            "issues": result.get("issues", []),
            "suggestions": result.get("suggestions", []),
            "overall_score": result.get("score"),
            "summary": result.get("summary"),
            "metadata": result.get("metadata")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code review failed: {str(e)}"
        )


@router.post("/code/optimize")
async def optimize_code(
    request: CodeOptimizationRequest,
    current_user=Depends(get_current_user)
):
    """Optimize code for performance and efficiency."""
    try:
        result = await code_service.optimize_code(
            code=request.code,
            language=request.language,
            optimization_goals=request.optimization_goals,
            preserve_functionality=request.preserve_functionality
        )
        
        return {
            "optimization_id": result.get("id"),
            "optimized_code": result.get("optimized_code"),
            "improvements": result.get("improvements", []),
            "performance_gain": result.get("performance_gain"),
            "explanation": result.get("explanation"),
            "metadata": result.get("metadata")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code optimization failed: {str(e)}"
        )


@router.post("/code/explain")
async def explain_code(
    request: CodeExplanationRequest,
    current_user=Depends(get_current_user)
):
    """Explain how code works."""
    try:
        result = await code_service.explain_code(
            code=request.code,
            language=request.language,
            detail_level=request.detail_level,
            include_examples=request.include_examples
        )
        
        return {
            "explanation_id": result.get("id"),
            "explanation": result.get("explanation"),
            "key_concepts": result.get("key_concepts", []),
            "examples": result.get("examples", []),
            "complexity_analysis": result.get("complexity_analysis"),
            "metadata": result.get("metadata")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code explanation failed: {str(e)}"
        )


@router.get("/code/snippets")
async def get_user_code_snippets(
    limit: int = 20,
    offset: int = 0,
    language: Optional[str] = None,
    current_user=Depends(get_current_user),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Get user's saved code snippets."""
    try:
        # Get user ID from Supabase user object
        user_id = current_user.get("id") or current_user.get("sub") or str(current_user.get("email", "unknown"))
        
        snippets = await repo_manager.code_repo.get_user_code_snippets(
            user_id=user_id,
            limit=limit,
            offset=offset,
            language=language
        )
        
        return {
            "snippets": [
                {
                    "id": str(snippet.id),
                    "code": snippet.code,
                    "language": snippet.language,
                    "description": snippet.description,
                    "created_at": snippet.created_at.isoformat(),
                    "metadata": snippet.metadata
                }
                for snippet in snippets
            ],
            "total": len(snippets)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve code snippets: {str(e)}"
        )


@router.get("/code/languages")
async def get_supported_languages(current_user=Depends(get_current_user)):
    """Get list of supported programming languages."""
    return {
        "languages": [
            {"name": "Python", "id": "python", "extensions": [".py"]},
            {"name": "JavaScript", "id": "javascript", "extensions": [".js", ".mjs"]},
            {"name": "TypeScript", "id": "typescript", "extensions": [".ts"]},
            {"name": "Java", "id": "java", "extensions": [".java"]},
            {"name": "C++", "id": "cpp", "extensions": [".cpp", ".cc", ".cxx"]},
            {"name": "C", "id": "c", "extensions": [".c"]},
            {"name": "C#", "id": "csharp", "extensions": [".cs"]},
            {"name": "Go", "id": "go", "extensions": [".go"]},
            {"name": "Rust", "id": "rust", "extensions": [".rs"]},
            {"name": "PHP", "id": "php", "extensions": [".php"]},
            {"name": "Ruby", "id": "ruby", "extensions": [".rb"]},
            {"name": "Swift", "id": "swift", "extensions": [".swift"]},
            {"name": "Kotlin", "id": "kotlin", "extensions": [".kt"]},
            {"name": "HTML", "id": "html", "extensions": [".html", ".htm"]},
            {"name": "CSS", "id": "css", "extensions": [".css"]},
            {"name": "SQL", "id": "sql", "extensions": [".sql"]},
            {"name": "Bash", "id": "bash", "extensions": [".sh"]},
            {"name": "PowerShell", "id": "powershell", "extensions": [".ps1"]},
            {"name": "R", "id": "r", "extensions": [".r", ".R"]},
            {"name": "MATLAB", "id": "matlab", "extensions": [".m"]}
        ]
    }


@router.delete("/code/snippets/{snippet_id}")
async def delete_code_snippet(
    snippet_id: str,
    current_user=Depends(get_current_user),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Delete a code snippet."""
    try:
        # Get user ID from Supabase user object
        user_id = current_user.get("id") or current_user.get("sub") or str(current_user.get("email", "unknown"))
        
        success = await repo_manager.code_repo.delete_code_snippet(
            snippet_id, 
            user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Code snippet not found"
            )
        
        # Decrement user stats
        await repo_manager.stats_repo.increment_stats(
            user_id, 
            "total_codes",
            -1
        )
        
        return {"message": "Code snippet deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete code snippet: {str(e)}"
        )