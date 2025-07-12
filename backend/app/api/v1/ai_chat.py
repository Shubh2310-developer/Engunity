"""AI Chat API endpoints using Groq llama-3.3-70b-versatile model."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.responses import StreamingResponse
import json

from ...services.auth_service import SupabaseAuthService
from ...services.groq_service import create_groq_completion, create_groq_stream, get_groq_service
from ...services.api_key_service import APIKeyService
from ...db.repositories.mongo_repository import get_repository_manager, RepositoryManager
from ...models.mongo_models import ChatMessage
from ...models.user import User
from ...core.deps import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

router = APIRouter()
security = HTTPBearer()
auth_service = SupabaseAuthService()


class ChatCompletionRequest(BaseModel):
    """Request schema for chat completion."""
    messages: List[Dict[str, str]] = Field(..., description="Chat messages")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=2048, ge=1, le=8192, description="Maximum tokens to generate")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Top-p sampling")
    stream: bool = Field(default=False, description="Stream the response")
    chat_id: Optional[str] = Field(default=None, description="Chat ID to save message to")
    save_conversation: bool = Field(default=True, description="Save conversation to database")
    system_prompt: Optional[str] = Field(default=None, description="Custom system prompt")
    conversation_context: Optional[List[Dict[str, str]]] = Field(default=None, description="Previous conversation context")


class ChatCompletionResponse(BaseModel):
    """Response schema for chat completion."""
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None


async def get_current_user_from_token(token: str = Depends(security)):
    """Get current user from token."""
    user = await auth_service.get_user_by_token(token.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user


@router.post("/ai/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    current_user=Depends(get_current_user_from_token),
    repo_manager: RepositoryManager = Depends(get_repository_manager),
    db: Session = Depends(get_db)
):
    """Create a chat completion using Groq llama-3.3-70b-versatile model."""
    try:
        # Get user's Groq API key if available, otherwise use fallback keys
        api_key_service = APIKeyService(db)
        
        # Map Supabase user to local user for API key lookup
        local_user = db.query(User).filter(User.email == current_user.get("email")).first()
        if not local_user:
            # Create user if doesn't exist
            local_user = User(
                email=current_user.get("email"),
                full_name=current_user.get("user_metadata", {}).get("full_name", ""),
                hashed_password="",  # Not used for Supabase users
                is_active=True,
                is_verified=True
            )
            db.add(local_user)
            db.commit()
            db.refresh(local_user)
        
        try:
            groq_api_key, provider = await api_key_service.get_working_api_key(local_user.id, "groq")
        except ValueError:
            # No API key found, will use fallback from environment
            groq_api_key = None
        
        if request.stream:
            # Prepare messages with context and system prompt
            prepared_messages = prepare_messages(
                request.messages, 
                request.system_prompt, 
                request.conversation_context
            )
            
            # Return streaming response
            return StreamingResponse(
                stream_chat_completion(prepared_messages, request, local_user, repo_manager, groq_api_key),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*"
                }
            )
        else:
            # Prepare messages with context and system prompt
            prepared_messages = prepare_messages(
                request.messages, 
                request.system_prompt, 
                request.conversation_context
            )
            
            # Create completion
            completion = await create_groq_completion(
                messages=prepared_messages,
                api_key=groq_api_key,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                stream=False
            )
            
            # Save conversation if requested
            if request.save_conversation and request.chat_id:
                await save_conversation_messages(
                    chat_id=request.chat_id,
                    messages=request.messages,
                    completion=completion,
                    user_id=local_user.id,
                    repo_manager=repo_manager
                )
            
            return completion
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat completion failed: {str(e)}"
        )


async def stream_chat_completion(
    prepared_messages: List[Dict[str, str]],
    request: ChatCompletionRequest,
    local_user: User,
    repo_manager: RepositoryManager,
    groq_api_key: Optional[str]
):
    """Stream chat completion response."""
    try:
        full_response = ""
        
        async for chunk in create_groq_stream(
            messages=prepared_messages,
            api_key=groq_api_key,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p
        ):
            # Extract content from chunk
            if chunk.get("choices") and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    full_response += content
                    yield f"data: {json.dumps(chunk)}\n\n"
        
        # Send completion marker
        yield "data: [DONE]\n\n"
        
        # Save conversation if requested
        if request.save_conversation and request.chat_id and full_response:
            # Create a mock completion object for saving
            mock_completion = {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": full_response
                    }
                }]
            }
            
            await save_conversation_messages(
                chat_id=request.chat_id,
                messages=request.messages,
                completion=mock_completion,
                user_id=local_user.id,
                repo_manager=repo_manager
            )
            
    except Exception as e:
        error_chunk = {
            "error": {
                "message": str(e),
                "type": "stream_error"
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"


async def save_conversation_messages(
    chat_id: str,
    messages: List[Dict[str, str]],
    completion: Dict,
    user_id: str,
    repo_manager: RepositoryManager
):
    """Save conversation messages to database."""
    try:
        # Save user message (last message in the list)
        if messages:
            last_user_message = messages[-1]
            if last_user_message.get("role") == "user":
                user_msg = ChatMessage(
                    role="user",
                    content=last_user_message["content"],
                    message_type="text"
                )
                await repo_manager.chat_repo.add_message(chat_id, user_msg)
        
        # Save assistant response
        if completion.get("choices") and len(completion["choices"]) > 0:
            assistant_content = completion["choices"][0]["message"]["content"]
            assistant_msg = ChatMessage(
                role="assistant",
                content=assistant_content,
                message_type="text",
                metadata={"model": "llama-3.3-70b-versatile", "provider": "groq"}
            )
            await repo_manager.chat_repo.add_message(chat_id, assistant_msg)
        
        # Update user stats
        await repo_manager.stats_repo.increment_stats(user_id, "total_messages", 2)
        
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error saving conversation: {e}")


@router.get("/ai/models")
async def get_available_models(current_user=Depends(get_current_user_from_token)):
    """Get available AI models."""
    try:
        service = get_groq_service()
        models = service.get_available_models()
        current_model = service.get_model_info()
        
        return {
            "available_models": models,
            "current_model": current_model,
            "default_model": "llama-3.3-70b-versatile"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get models: {str(e)}"
        )


@router.post("/ai/validate-key")
async def validate_groq_key(
    api_key: str,
    current_user=Depends(get_current_user_from_token)
):
    """Validate a Groq API key."""
    try:
        service = get_groq_service(api_key)
        is_valid = await service.validate_api_key()
        
        return {
            "is_valid": is_valid,
            "provider": "groq",
            "model": "llama-3.3-70b-versatile"
        }
        
    except Exception as e:
        return {
            "is_valid": False,
            "error": str(e),
            "provider": "groq"
        }


@router.get("/ai/usage")
async def get_ai_usage_stats(
    current_user=Depends(get_current_user_from_token),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Get AI usage statistics for the current user."""
    try:
        stats = await repo_manager.stats_repo.get_user_stats(current_user["id"])
        
        if not stats:
            return {
                "total_messages": 0,
                "total_chats": 0,
                "current_model": "llama-3.3-70b-versatile",
                "provider": "groq"
            }
        
        return {
            "total_messages": stats.total_messages,
            "total_chats": stats.total_chats,
            "total_codes": stats.total_codes,
            "total_images": stats.total_images,
            "total_pdfs": stats.total_pdfs,
            "storage_used": stats.storage_used,
            "last_activity": stats.last_activity,
            "current_model": "llama-3.3-70b-versatile",
            "provider": "groq"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage stats: {str(e)}"
        )


def prepare_messages(
    messages: List[Dict[str, str]], 
    system_prompt: Optional[str] = None,
    conversation_context: Optional[List[Dict[str, str]]] = None
) -> List[Dict[str, str]]:
    """Prepare messages with system prompt and conversation context."""
    prepared_messages = []
    
    # Add system prompt if provided
    if system_prompt:
        prepared_messages.append({
            "role": "system",
            "content": system_prompt
        })
    else:
        # Default system prompt for enhanced chat
        prepared_messages.append({
            "role": "system",
            "content": """You are an advanced AI assistant powered by Llama 3.3 70B. You are helpful, harmless, and honest. 

Key capabilities:
- Expert-level knowledge across various domains
- Code generation and debugging
- Research and analysis
- Creative writing and problem-solving
- Technical explanations and tutorials

Guidelines:
- Provide accurate, well-structured responses
- Include code examples when relevant
- Ask clarifying questions when needed
- Be concise but comprehensive
- Adapt your communication style to the user's level"""
        })
    
    # Add conversation context if provided
    if conversation_context:
        # Limit context to last 10 messages to manage token usage
        recent_context = conversation_context[-10:]
        prepared_messages.extend(recent_context)
    
    # Add current messages
    prepared_messages.extend(messages)
    
    return prepared_messages


@router.post("/ai/chat/enhanced")
async def create_enhanced_chat(
    request: ChatCompletionRequest,
    current_user=Depends(get_current_user_from_token),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Enhanced chat endpoint with conversation context and specialized prompts."""
    try:
        # Get conversation history if chat_id is provided
        conversation_context = []
        if request.chat_id:
            chat = await repo_manager.chat_repo.get_chat_by_id(request.chat_id)
            if chat and chat.user_id == current_user["id"]:
                # Convert chat history to messages format
                conversation_context = [
                    {
                        "role": msg.role,
                        "content": msg.content
                    }
                    for msg in chat.messages[-20:]  # Last 20 messages for context
                ]
        
        # Update request with context
        enhanced_request = ChatCompletionRequest(
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            stream=request.stream,
            chat_id=request.chat_id,
            save_conversation=request.save_conversation,
            system_prompt=request.system_prompt,
            conversation_context=conversation_context
        )
        
        # Use the existing completion endpoint
        return await create_chat_completion(enhanced_request, current_user, repo_manager)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhanced chat failed: {str(e)}"
        )


@router.post("/ai/chat/specialized")
async def create_specialized_chat(
    prompt: str,
    chat_type: str,  # "code", "research", "creative", "technical", "casual"
    current_user=Depends(get_current_user_from_token),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Specialized chat endpoint with predefined system prompts for different use cases."""
    
    specialized_prompts = {
        "code": """You are an expert software engineer and code mentor. Your role is to:
- Generate clean, efficient, and well-documented code
- Explain complex programming concepts clearly
- Provide debugging assistance and optimization suggestions
- Follow best practices and security guidelines
- Include error handling and edge cases
- Suggest testing approaches

Format code responses with proper syntax highlighting and explanations.""",

        "research": """You are a research assistant with expertise across multiple academic domains. Your role is to:
- Provide comprehensive, well-sourced information
- Analyze complex topics from multiple perspectives
- Identify key insights and patterns
- Suggest further research directions
- Present information in a structured, academic format
- Include relevant citations and references when possible

Be thorough, objective, and analytically rigorous.""",

        "creative": """You are a creative writing assistant and brainstorming partner. Your role is to:
- Generate original, engaging creative content
- Provide inspiration and creative prompts
- Help develop characters, plots, and narratives
- Suggest creative solutions to problems
- Adapt writing style to different genres and audiences
- Provide constructive feedback on creative works

Be imaginative, encouraging, and supportive of creative exploration.""",

        "technical": """You are a technical expert and documentation specialist. Your role is to:
- Explain complex technical concepts clearly
- Create comprehensive technical documentation
- Provide step-by-step tutorials and guides
- Troubleshoot technical issues systematically
- Recommend tools and best practices
- Ensure accuracy and precision in technical details

Be precise, methodical, and educational in your approach.""",

        "casual": """You are a friendly and knowledgeable conversational AI. Your role is to:
- Engage in natural, helpful conversations
- Provide information in an accessible way
- Be supportive and encouraging
- Show genuine interest in helping users
- Adapt to the user's communication style
- Make complex topics understandable

Be warm, approachable, and genuinely helpful."""
    }
    
    system_prompt = specialized_prompts.get(chat_type, specialized_prompts["casual"])
    
    request = ChatCompletionRequest(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt,
        temperature=0.7,
        max_tokens=2048
    )
    
    try:
        return await create_chat_completion(request, current_user, repo_manager)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Specialized chat failed: {str(e)}"
        )


@router.get("/ai/chat/types")
async def get_chat_types(current_user=Depends(get_current_user_from_token)):
    """Get available specialized chat types."""
    return {
        "chat_types": [
            {
                "id": "code",
                "name": "Code Assistant",
                "description": "Expert programming help and code generation",
                "icon": "💻"
            },
            {
                "id": "research",
                "name": "Research Assistant",
                "description": "Academic research and comprehensive analysis",
                "icon": "📚"
            },
            {
                "id": "creative",
                "name": "Creative Writing",
                "description": "Creative content and brainstorming support",
                "icon": "✨"
            },
            {
                "id": "technical",
                "name": "Technical Expert",
                "description": "Technical documentation and troubleshooting",
                "icon": "🔧"
            },
            {
                "id": "casual",
                "name": "General Chat",
                "description": "Friendly conversation and general assistance",
                "icon": "💬"
            }
        ]
    }

