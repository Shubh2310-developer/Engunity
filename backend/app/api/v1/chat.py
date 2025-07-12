"""Chat API endpoints with MongoDB integration."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from ...services.auth_service import SupabaseAuthService
from ...db.repositories.mongo_repository import get_repository_manager, RepositoryManager
from ...models.mongo_models import ChatHistory, ChatMessage
from ...schemas.chat import (
    ChatCreateRequest, ChatResponse, ChatListResponse, 
    MessageCreateRequest, MessageResponse
)

router = APIRouter()
security = HTTPBearer()
auth_service = SupabaseAuthService()


async def get_current_user(token: str = Depends(security)):
    """Get current user from token."""
    user = await auth_service.get_user_by_token(token.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user


@router.post("/chats", response_model=ChatResponse)
async def create_chat(
    request: ChatCreateRequest,
    current_user=Depends(get_current_user),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Create a new chat."""
    try:
        chat_id = await repo_manager.chat_repo.create_chat(
            user_id=current_user["id"],
            title=request.title
        )
        
        # Increment user stats
        await repo_manager.stats_repo.increment_stats(
            current_user["id"], 
            "total_chats"
        )
        
        chat = await repo_manager.chat_repo.get_chat_by_id(chat_id)
        return ChatResponse.from_chat_history(chat)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat"
        )


@router.get("/chats", response_model=ChatListResponse)
async def get_user_chats(
    limit: int = 20,
    offset: int = 0,
    current_user=Depends(get_current_user),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Get user's chats."""
    try:
        chats = await repo_manager.chat_repo.get_user_chats(
            user_id=current_user["id"],
            limit=limit,
            offset=offset
        )
        
        return ChatListResponse(
            chats=[ChatResponse.from_chat_history(chat) for chat in chats],
            total=len(chats)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chats"
        )


@router.get("/chats/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    current_user=Depends(get_current_user),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Get a specific chat."""
    try:
        chat = await repo_manager.chat_repo.get_chat_by_id(chat_id)
        
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        if chat.user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return ChatResponse.from_chat_history(chat)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat"
        )


@router.post("/chats/{chat_id}/messages", response_model=MessageResponse)
async def add_message(
    chat_id: str,
    request: MessageCreateRequest,
    current_user=Depends(get_current_user),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Add a message to a chat."""
    try:
        # Verify chat exists and user owns it
        chat = await repo_manager.chat_repo.get_chat_by_id(chat_id)
        if not chat or chat.user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        message = ChatMessage(
            role=request.role,
            content=request.content,
            message_type=request.message_type,
            metadata=request.metadata
        )
        
        success = await repo_manager.chat_repo.add_message(chat_id, message)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add message"
            )
        
        # Increment user stats
        await repo_manager.stats_repo.increment_stats(
            current_user["id"], 
            "total_messages"
        )
        
        return MessageResponse(
            role=message.role,
            content=message.content,
            timestamp=message.timestamp,
            message_type=message.message_type,
            metadata=message.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add message"
        )


@router.put("/chats/{chat_id}/title")
async def update_chat_title(
    chat_id: str,
    title: str,
    current_user=Depends(get_current_user),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Update chat title."""
    try:
        # Verify chat exists and user owns it
        chat = await repo_manager.chat_repo.get_chat_by_id(chat_id)
        if not chat or chat.user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        success = await repo_manager.chat_repo.update_chat_title(chat_id, title)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update chat title"
            )
        
        return {"message": "Chat title updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update chat title"
        )


@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: str,
    current_user=Depends(get_current_user),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Delete a chat."""
    try:
        success = await repo_manager.chat_repo.delete_chat(chat_id, current_user["id"])
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        # Decrement user stats
        await repo_manager.stats_repo.increment_stats(
            current_user["id"], 
            "total_chats",
            -1
        )
        
        return {"message": "Chat deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat"
        )


@router.put("/chats/{chat_id}/archive")
async def archive_chat(
    chat_id: str,
    current_user=Depends(get_current_user),
    repo_manager: RepositoryManager = Depends(get_repository_manager)
):
    """Archive a chat."""
    try:
        success = await repo_manager.chat_repo.archive_chat(chat_id, current_user["id"])
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        return {"message": "Chat archived successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to archive chat"
        )