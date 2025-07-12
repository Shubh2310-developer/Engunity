"""Chat schema definitions."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ..models.mongo_models import ChatHistory


class ChatCreateRequest(BaseModel):
    """Request schema for creating a new chat."""
    title: str = Field(..., min_length=1, max_length=200, description="Chat title")


class MessageCreateRequest(BaseModel):
    """Request schema for creating a new message."""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., min_length=1, description="Message content")
    message_type: str = Field(default="text", description="Message type")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class MessageResponse(BaseModel):
    """Response schema for a chat message."""
    role: str
    content: str
    timestamp: datetime
    message_type: str
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response schema for a chat."""
    id: str
    title: str
    messages: List[MessageResponse]
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    is_archived: bool
    
    @classmethod
    def from_chat_history(cls, chat: ChatHistory) -> "ChatResponse":
        """Create ChatResponse from ChatHistory model."""
        return cls(
            id=str(chat.id),
            title=chat.title,
            messages=[
                MessageResponse(
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.timestamp,
                    message_type=msg.message_type,
                    metadata=msg.metadata
                )
                for msg in chat.messages
            ],
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            tags=chat.tags,
            is_archived=chat.is_archived
        )


class ChatListResponse(BaseModel):
    """Response schema for a list of chats."""
    chats: List[ChatResponse]
    total: int


class ChatSummaryResponse(BaseModel):
    """Response schema for chat summary (without messages)."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    tags: List[str]
    is_archived: bool
    
    @classmethod
    def from_chat_history(cls, chat: ChatHistory) -> "ChatSummaryResponse":
        """Create ChatSummaryResponse from ChatHistory model."""
        return cls(
            id=str(chat.id),
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            message_count=len(chat.messages),
            tags=chat.tags,
            is_archived=chat.is_archived
        )