"""Integrated Chat API that combines AI chat and code generation."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.responses import StreamingResponse
import json
import re
from datetime import datetime

from ...services.auth_service import SupabaseAuthService
from ...services.groq_service import create_groq_completion, create_groq_stream
from ...services.code_service import CodeGenerationService
from ...db.repositories.mongo_repository import get_repository_manager, RepositoryManager
from ...models.mongo_models import ChatMessage, CodeSnippet
from pydantic import BaseModel, Field

router = APIRouter()
security = HTTPBearer()
auth_service = SupabaseAuthService()
code_service = CodeGenerationService()


class IntegratedChatRequest(BaseModel):
    """Request schema for integrated chat."""
    message: str = Field(..., description="User message")
    chat_id: Optional[str] = Field(default=None, description="Chat ID")
    conversation_context: Optional[List[Dict[str, str]]] = Field(default=None, description="Previous conversation context")
    save_conversation: bool = Field(default=True, description="Save conversation to database")
    auto_detect_code: bool = Field(default=True, description="Automatically detect code requests")


class IntegratedChatResponse(BaseModel):
    """Response schema for integrated chat."""
    response: str = Field(..., description="AI response")
    response_type: str = Field(..., description="Type of response: 'chat' or 'code'")
    chat_id: str = Field(..., description="Chat ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    code_snippets: Optional[List[Dict[str, Any]]] = Field(default=None, description="Generated code snippets")


async def get_current_user(token: str = Depends(security)):
    """Get current user from token."""
    user = await auth_service.get_user_by_token(token.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user


@router.post("/integrated-chat-test")
async def integrated_chat_test(
    request: IntegratedChatRequest,
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Test integrated chat without authentication."""
    try:
        # Use a test user ID
        user_id = "test_user_123"
        
        # Create chat if needed
        chat_id = request.chat_id
        if not chat_id:
            chat_title = generate_chat_title(request.message)
            chat_id = await repo_manager.chat_repo.create_chat(user_id, chat_title)
        
        # Detect if this is a code-related request
        is_code_request = detect_code_request(request.message) if request.auto_detect_code else False
        
        response_type = "code" if is_code_request else "chat"
        response_content = ""
        metadata = {}
        code_snippets = []
        
        if is_code_request:
            # Handle code generation
            code_result = await handle_code_generation(request.message, user_id, chat_id, repo_manager)
            response_content = code_result["response"]
            metadata = code_result["metadata"]
            code_snippets = code_result["code_snippets"]
        else:
            # Handle regular chat
            chat_result = await handle_chat_completion(request, user_id, chat_id, repo_manager)
            response_content = chat_result["response"]
            metadata = chat_result["metadata"]
        
        # Save conversation to MongoDB
        if request.save_conversation:
            await save_conversation_to_mongo(
                chat_id=chat_id,
                user_message=request.message,
                assistant_response=response_content,
                user_id=user_id,
                response_type=response_type,
                metadata=metadata,
                repo_manager=repo_manager
            )
        
        return {
            "response": response_content,
            "response_type": response_type,
            "chat_id": chat_id,
            "metadata": metadata,
            "code_snippets": code_snippets
        }
        
    except Exception as e:
        import traceback
        error_details = f"Integrated chat failed: {str(e)}"
        print(f"Integrated chat error: {error_details}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_details
        )


@router.post("/integrated-chat")
async def integrated_chat(
    request: IntegratedChatRequest,
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Handle integrated chat - temporarily without authentication for testing."""
    try:
        # Use a default user ID for testing
        user_id = "default_user_123"
        
        # Create chat if needed
        chat_id = request.chat_id
        if not chat_id:
            chat_title = generate_chat_title(request.message)
            chat_id = await repo_manager.chat_repo.create_chat(user_id, chat_title)
        
        # Detect if this is a code-related request
        is_code_request = detect_code_request(request.message) if request.auto_detect_code else False
        
        response_type = "code" if is_code_request else "chat"
        response_content = ""
        metadata = {}
        code_snippets = []
        
        if is_code_request:
            # Handle code generation
            code_result = await handle_code_generation(request.message, user_id, chat_id, repo_manager)
            response_content = code_result["response"]
            metadata = code_result["metadata"]
            code_snippets = code_result["code_snippets"]
        else:
            # Handle regular chat
            chat_result = await handle_chat_completion(request, user_id, chat_id, repo_manager)
            response_content = chat_result["response"]
            metadata = chat_result["metadata"]
        
        # Save conversation to MongoDB
        if request.save_conversation:
            await save_conversation_to_mongo(
                chat_id=chat_id,
                user_message=request.message,
                assistant_response=response_content,
                user_id=user_id,
                response_type=response_type,
                metadata=metadata,
                repo_manager=repo_manager
            )
        
        return {
            "response": response_content,
            "response_type": response_type,
            "chat_id": chat_id,
            "metadata": metadata,
            "code_snippets": code_snippets
        }
        
    except Exception as e:
        import traceback
        error_details = f"Integrated chat failed: {str(e)}"
        print(f"Integrated chat error: {error_details}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_details
        )


@router.post("/integrated-chat-auth", response_model=IntegratedChatResponse)
async def integrated_chat_auth(
    request: IntegratedChatRequest,
    current_user=Depends(get_current_user),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Handle integrated chat with automatic code generation detection."""
    try:
        # Get user ID - handle both dict and User object
        if hasattr(current_user, 'id'):
            user_id = current_user.id
        elif hasattr(current_user, 'get'):
            user_id = current_user.get("id") or current_user.get("sub") or str(current_user.get("email", "unknown"))
        else:
            user_id = getattr(current_user, 'sub', None) or getattr(current_user, 'email', 'unknown')
        
        # Create chat if needed
        chat_id = request.chat_id
        if not chat_id:
            chat_title = generate_chat_title(request.message)
            chat_id = await repo_manager.chat_repo.create_chat(user_id, chat_title)
        
        # Detect if this is a code-related request
        is_code_request = detect_code_request(request.message) if request.auto_detect_code else False
        
        response_type = "code" if is_code_request else "chat"
        response_content = ""
        metadata = {}
        code_snippets = []
        
        if is_code_request:
            # Handle code generation
            code_result = await handle_code_generation(request.message, user_id, chat_id, repo_manager)
            response_content = code_result["response"]
            metadata = code_result["metadata"]
            code_snippets = code_result["code_snippets"]
        else:
            # Handle regular chat
            chat_result = await handle_chat_completion(request, user_id, chat_id, repo_manager)
            response_content = chat_result["response"]
            metadata = chat_result["metadata"]
        
        # Save conversation to MongoDB
        if request.save_conversation:
            await save_conversation_to_mongo(
                chat_id=chat_id,
                user_message=request.message,
                assistant_response=response_content,
                user_id=user_id,
                response_type=response_type,
                metadata=metadata,
                repo_manager=repo_manager
            )
        
        return IntegratedChatResponse(
            response=response_content,
            response_type=response_type,
            chat_id=chat_id,
            metadata=metadata,
            code_snippets=code_snippets
        )
        
    except Exception as e:
        import traceback
        error_details = f"Integrated chat failed: {str(e)}"
        print(f"Integrated chat error: {error_details}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_details
        )


def detect_code_request(message: str) -> bool:
    """Detect if the message is asking for code generation."""
    code_indicators = [
        # Direct code requests
        r'\b(write|create|generate|build|implement|code|program|script)\b.*\b(function|class|algorithm|program|script|code)\b',
        r'\b(how to|can you)\b.*\b(code|implement|create|write|build)\b',
        
        # Language specific
        r'\b(python|javascript|java|c\+\+|html|css|sql|php|ruby|go|rust|swift)\b.*\b(code|function|class|script)\b',
        
        # Programming concepts
        r'\b(debug|fix|optimize|refactor|review)\b.*\b(code|function|algorithm)\b',
        r'\b(data structure|algorithm|sorting|search|recursion|loop)\b',
        
        # Code patterns
        r'```|`[^`]+`',  # Markdown code blocks or inline code
        r'\bdef\s+\w+\(|\bfunction\s+\w+\(|\bclass\s+\w+\b',  # Code syntax
    ]
    
    message_lower = message.lower()
    
    for pattern in code_indicators:
        if re.search(pattern, message_lower, re.IGNORECASE):
            return True
    
    return False


async def handle_code_generation(message: str, user_id: str, chat_id: str, repo_manager: RepositoryManager) -> Dict[str, Any]:
    """Handle code generation requests."""
    
    # Extract language from message
    language = extract_language_from_message(message)
    
    # Generate code using the code service
    result = await code_service.generate_code(
        prompt=message,
        language=language,
        complexity="intermediate",
        include_comments=True,
        include_tests=False,
        max_tokens=2048,
        temperature=0.3
    )
    
    # Save code snippet to MongoDB
    code_snippet = CodeSnippet(
        user_id=user_id,
        title=generate_code_title(message),
        description=message,
        language=language,
        code=result["code"],
        chat_id=chat_id,
        metadata={
            "generated_from_chat": True,
            "original_prompt": message,
            "tokens_used": result.get("tokens_used", 0)
        }
    )
    
    code_id = await repo_manager.code_repo.save_code_snippet(user_id, code_snippet)
    
    # Format response
    response = f"I've generated {language} code for you:\n\n"
    if result.get("explanation"):
        response += f"{result['explanation']}\n\n"
    
    response += f"```{language}\n{result['code']}\n```"
    
    # Update user stats
    await repo_manager.stats_repo.increment_stats(user_id, "total_codes")
    
    return {
        "response": response,
        "metadata": {
            "type": "code_generation",
            "language": language,
            "code_id": code_id,
            "tokens_used": result.get("tokens_used", 0)
        },
        "code_snippets": [{
            "id": code_id,
            "language": language,
            "code": result["code"],
            "explanation": result.get("explanation", "")
        }]
    }


async def handle_chat_completion(request: IntegratedChatRequest, user_id: str, chat_id: str, repo_manager: RepositoryManager) -> Dict[str, Any]:
    """Handle regular chat completion."""
    
    # Build conversation context
    messages = []
    
    # Add system prompt
    messages.append({
        "role": "system",
        "content": """You are an advanced AI assistant specialized in programming and software development. 
        You can help with coding questions, explain programming concepts, debug code, and provide technical guidance.
        If a user asks for code generation, be helpful and provide clear, well-commented code examples.
        Always be concise but thorough in your explanations."""
    })
    
    # Add conversation context if provided
    if request.conversation_context:
        messages.extend(request.conversation_context[-10:])  # Last 10 messages
    
    # Add current message
    messages.append({"role": "user", "content": request.message})
    
    # Get completion from Groq
    response = await create_groq_completion(
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
        top_p=0.9
    )
    
    content = response["choices"][0]["message"]["content"]
    
    return {
        "response": content,
        "metadata": {
            "type": "chat_completion",
            "tokens_used": response.get("usage", {}).get("total_tokens", 0),
            "model": "llama-3.3-70b-versatile"
        }
    }


async def save_conversation_to_mongo(
    chat_id: str,
    user_message: str,
    assistant_response: str,
    user_id: str,
    response_type: str,
    metadata: Dict[str, Any],
    repo_manager: RepositoryManager
):
    """Save conversation to MongoDB."""
    try:
        # Save user message
        user_msg = ChatMessage(
            role="user",
            content=user_message,
            message_type="text",
            metadata={"timestamp": datetime.utcnow().isoformat()}
        )
        await repo_manager.chat_repo.add_message(chat_id, user_msg)
        
        # Save assistant response
        assistant_msg = ChatMessage(
            role="assistant",
            content=assistant_response,
            message_type=response_type,
            metadata={
                **metadata,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        await repo_manager.chat_repo.add_message(chat_id, assistant_msg)
        
        # Update user stats
        await repo_manager.stats_repo.increment_stats(user_id, "total_messages", 2)  # User + assistant message
        
    except Exception as e:
        print(f"Error saving conversation to MongoDB: {e}")


def extract_language_from_message(message: str) -> str:
    """Extract programming language from user message."""
    languages = {
        'python': ['python', 'py', 'django', 'flask', 'pandas', 'numpy'],
        'javascript': ['javascript', 'js', 'node', 'react', 'vue', 'angular', 'express'],
        'java': ['java', 'spring', 'android'],
        'cpp': ['c++', 'cpp', 'c plus plus'],
        'c': ['c language', ' c '],
        'html': ['html', 'web page', 'webpage'],
        'css': ['css', 'styling', 'styles'],
        'sql': ['sql', 'database', 'query', 'mysql', 'postgresql'],
        'php': ['php', 'laravel'],
        'ruby': ['ruby', 'rails'],
        'go': ['golang', 'go '],
        'rust': ['rust'],
        'swift': ['swift', 'ios'],
        'kotlin': ['kotlin'],
        'typescript': ['typescript', 'ts'],
        'bash': ['bash', 'shell', 'terminal']
    }
    
    message_lower = message.lower()
    
    for lang, keywords in languages.items():
        if any(keyword in message_lower for keyword in keywords):
            return lang
    
    return 'python'  # Default to Python


def generate_chat_title(message: str) -> str:
    """Generate a title for the chat based on the first message."""
    # Take first 50 characters and clean up
    title = message[:50].strip()
    if len(message) > 50:
        title += "..."
    
    # Remove newlines and extra spaces
    title = re.sub(r'\s+', ' ', title)
    
    return title


def generate_code_title(message: str) -> str:
    """Generate a title for code snippet based on the request."""
    # Extract key terms
    key_terms = re.findall(r'\b(function|class|algorithm|sort|search|calculator|converter|parser|validator|generator)\b', message.lower())
    
    if key_terms:
        return f"{key_terms[0].title()} - {message[:30]}..."
    
    return f"Code - {message[:40]}..."


@router.get("/chat-history/{chat_id}")
async def get_chat_history(
    chat_id: str,
    current_user=Depends(get_current_user),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Get chat history for a specific chat."""
    try:
        # Get user ID - handle both dict and User object
        if hasattr(current_user, 'id'):
            user_id = current_user.id
        elif hasattr(current_user, 'get'):
            user_id = current_user.get("id") or current_user.get("sub") or str(current_user.get("email", "unknown"))
        else:
            user_id = getattr(current_user, 'sub', None) or getattr(current_user, 'email', 'unknown')
        
        chat = await repo_manager.chat_repo.get_chat_by_id(chat_id)
        if not chat or chat.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        return {
            "chat_id": chat_id,
            "title": chat.title,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "message_type": msg.message_type,
                    "metadata": msg.metadata
                }
                for msg in chat.messages
            ],
            "created_at": chat.created_at.isoformat(),
            "updated_at": chat.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat history: {str(e)}"
        )


@router.get("/user-chats")
async def get_user_chats(
    limit: int = 20,
    offset: int = 0,
    current_user=Depends(get_current_user),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Get user's chat history."""
    try:
        # Get user ID - handle both dict and User object
        if hasattr(current_user, 'id'):
            user_id = current_user.id
        elif hasattr(current_user, 'get'):
            user_id = current_user.get("id") or current_user.get("sub") or str(current_user.get("email", "unknown"))
        else:
            user_id = getattr(current_user, 'sub', None) or getattr(current_user, 'email', 'unknown')
        
        chats = await repo_manager.chat_repo.get_user_chats(user_id, limit, offset)
        
        return {
            "chats": [
                {
                    "id": str(chat.id),
                    "title": chat.title,
                    "created_at": chat.created_at.isoformat(),
                    "updated_at": chat.updated_at.isoformat(),
                    "message_count": len(chat.messages)
                }
                for chat in chats
            ],
            "total": len(chats)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user chats: {str(e)}"
        )