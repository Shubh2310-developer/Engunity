# backend/app/schemas/document.py
"""
Pydantic schemas for document API request/response models.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator, root_validator


# Base schemas for common fields
class DocumentBase(BaseModel):
    """Base schema with common document fields."""
    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    description: Optional[str] = Field(None, max_length=1000, description="Document description")
    tags: List[str] = Field(default=[], description="Document tags for categorization")
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags format."""
        if v is None:
            return []
        # Remove empty tags and limit to 10 tags
        valid_tags = [tag.strip() for tag in v if tag.strip()][:10]
        return valid_tags
    
    @validator('title')
    def validate_title(cls, v):
        """Validate title format."""
        return v.strip()


# Request schemas
class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    language: Optional[str] = Field("en", description="Document language")
    is_public: Optional[bool] = Field(False, description="Whether document is publicly accessible")


class DocumentUpdate(BaseModel):
    """Schema for updating document metadata."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None)
    is_public: Optional[bool] = Field(None)
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags format."""
        if v is None:
            return v
        valid_tags = [tag.strip() for tag in v if tag.strip()][:10]
        return valid_tags


class DocumentQARequest(BaseModel):
    """Schema for document Q&A requests."""
    question: str = Field(..., min_length=1, max_length=1000, description="Question to ask about the document")
    max_chunks: Optional[int] = Field(5, ge=1, le=20, description="Maximum number of chunks to use for context")
    include_sources: Optional[bool] = Field(True, description="Whether to include source information")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")
    context_window: Optional[int] = Field(4000, ge=1000, le=8000, description="Context window size in tokens")
    
    @validator('question')
    def validate_question(cls, v):
        """Validate question format."""
        return v.strip()


class DocumentSummaryRequest(BaseModel):
    """Schema for document summarization requests."""
    summary_type: str = Field("comprehensive", regex="^(brief|comprehensive|key_points)$", description="Type of summary to generate")
    max_length: Optional[int] = Field(500, ge=100, le=2000, description="Maximum summary length in words")
    focus_areas: Optional[List[str]] = Field(default=[], description="Specific areas to focus on in summary")


class DocumentSearchRequest(BaseModel):
    """Schema for document search requests."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    max_results: Optional[int] = Field(10, ge=1, le=50, description="Maximum number of results to return")
    threshold: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Relevance threshold for results")


class BulkDeleteRequest(BaseModel):
    """Schema for bulk document deletion."""
    document_ids: List[UUID] = Field(..., min_items=1, max_items=50, description="List of document IDs to delete")


# Response schemas
class ContextSource(BaseModel):
    """Schema for context source information."""
    chunk_id: Optional[UUID] = Field(description="ID of the source chunk")
    page_number: Optional[int] = Field(description="Page number in the original document")
    content_preview: str = Field(description="Preview of the source content")
    relevance_score: float = Field(description="Relevance score for this source")
    
    class Config:
        schema_extra = {
            "example": {
                "chunk_id": "123e4567-e89b-12d3-a456-426614174000",
                "page_number": 1,
                "content_preview": "This section discusses the main findings...",
                "relevance_score": 0.85
            }
        }


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    id: UUID = Field(description="Document ID")
    filename: str = Field(description="Original filename")
    file_type: str = Field(description="MIME type")
    file_size: int = Field(description="File size in bytes")
    file_path: str = Field(description="Storage path")
    user_id: UUID = Field(description="Owner user ID")
    
    # Processing information
    processing_status: str = Field(description="Processing status")
    error_message: Optional[str] = Field(description="Error message if processing failed")
    processed_at: Optional[datetime] = Field(description="When processing completed")
    chunk_count: int = Field(description="Number of text chunks")
    total_tokens: int = Field(description="Total token count")
    
    # Metadata
    language: str = Field(description="Document language")
    is_public: bool = Field(description="Public accessibility")
    shared_with: List[UUID] = Field(description="Users document is shared with")
    
    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Research Paper on AI Ethics",
                "description": "Comprehensive analysis of ethical considerations in AI development",
                "filename": "ai_ethics_paper.pdf",
                "file_type": "application/pdf",
                "file_size": 2048576,
                "processing_status": "completed",
                "chunk_count": 25,
                "tags": ["AI", "Ethics", "Research"],
                "created_at": "2023-01-01T12:00:00Z"
            }
        }


class DocumentListResponse(BaseModel):
    """Schema for paginated document list response."""
    documents: List[DocumentResponse] = Field(description="List of documents")
    total: int = Field(description="Total number of documents")
    skip: int = Field(description="Number of documents skipped")
    limit: int = Field(description="Maximum number of documents returned")
    
    class Config:
        schema_extra = {
            "example": {
                "documents": [],
                "total": 150,
                "skip": 0,
                "limit": 50
            }
        }


class DocumentQAResponse(BaseModel):
    """Schema for document Q&A response."""
    answer: str = Field(description="Generated answer to the question")
    confidence_score: float = Field(description="Confidence score for the answer")
    sources: List[ContextSource] = Field(description="Source information used for the answer")
    processing_time: float = Field(description="Processing time in seconds")
    document_id: UUID = Field(description="Document ID")
    chunks_used: Optional[int] = Field(description="Number of chunks used for context")
    
    class Config:
        schema_extra = {
            "example": {
                "answer": "Based on the document, AI ethics involves consideration of fairness, transparency, and accountability in algorithmic decision-making.",
                "confidence_score": 0.92,
                "sources": [
                    {
                        "chunk_id": "123e4567-e89b-12d3-a456-426614174000",
                        "page_number": 1,
                        "content_preview": "AI ethics is a critical field...",
                        "relevance_score": 0.95
                    }
                ],
                "processing_time": 1.25,
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "chunks_used": 3
            }
        }


class DocumentSummaryResponse(BaseModel):
    """Schema for document summary response."""
    summary: str = Field(description="Generated summary")
    summary_type: str = Field(description="Type of summary generated")
    document_id: UUID = Field(description="Document ID")
    key_concepts: List[Dict[str, Any]] = Field(description="Key concepts extracted from document")
    generated_at: datetime = Field(description="When summary was generated")
    
    class Config:
        schema_extra = {
            "example": {
                "summary": "This paper presents a comprehensive analysis of AI ethics...",
                "summary_type": "comprehensive",
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "key_concepts": [
                    {
                        "concept": "Algorithmic Bias",
                        "description": "Systematic errors in AI systems",
                        "importance": 9.0
                    }
                ],
                "generated_at": "2023-01-01T12:00:00Z"
            }
        }


class DocumentSearchResponse(BaseModel):
    """Schema for document search response."""
    query: str = Field(description="Original search query")
    document_id: UUID = Field(description="Document ID")
    passages: List[Dict[str, Any]] = Field(description="Relevant passages found")
    total_found: int = Field(description="Total number of passages found")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "machine learning algorithms",
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "passages": [
                    {
                        "content": "Machine learning algorithms are computational methods...",
                        "page_number": 5,
                        "chunk_index": 12,
                        "relevance_score": 0.88,
                        "preview": "Machine learning algorithms are computational..."
                    }
                ],
                "total_found": 7
            }
        }


# Folder schemas
class DocumentFolderCreate(BaseModel):
    """Schema for creating document folders."""
    name: str = Field(..., min_length=1, max_length=255, description="Folder name")
    description: Optional[str] = Field(None, max_length=1000, description="Folder description")
    parent_id: Optional[UUID] = Field(None, description="Parent folder ID")
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$", description="Folder color (hex)")


class DocumentFolderResponse(BaseModel):
    """Schema for document folder response."""
    id: UUID = Field(description="Folder ID")
    name: str = Field(description="Folder name")
    description: Optional[str] = Field(description="Folder description")
    color: Optional[str] = Field(description="Folder color")
    parent_id: Optional[UUID] = Field(description="Parent folder ID")
    user_id: UUID = Field(description="Owner user ID")
    document_count: int = Field(description="Number of documents in folder")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    class Config:
        orm_mode = True


# Sharing schemas
class DocumentShareCreate(BaseModel):
    """Schema for sharing documents."""
    shared_with_id: UUID = Field(description="User ID to share with")
    can_read: bool = Field(True, description="Read permission")
    can_ask_questions: bool = Field(True, description="Q&A permission")
    can_edit: bool = Field(False, description="Edit permission")
    can_delete: bool = Field(False, description="Delete permission")
    share_message: Optional[str] = Field(None, max_length=500, description="Share message")
    expires_at: Optional[datetime] = Field(None, description="Share expiration")


class DocumentShareResponse(BaseModel):
    """Schema for document share response."""
    id: UUID = Field(description="Share ID")
    document_id: UUID = Field(description="Document ID")
    owner_id: UUID = Field(description="Owner user ID")
    shared_with_id: UUID = Field(description="Shared with user ID")
    can_read: bool = Field(description="Read permission")
    can_ask_questions: bool = Field(description="Q&A permission")
    can_edit: bool = Field(description="Edit permission")
    can_delete: bool = Field(description="Delete permission")
    share_message: Optional[str] = Field(description="Share message")
    expires_at: Optional[datetime] = Field(description="Share expiration")
    is_active: bool = Field(description="Share status")
    created_at: datetime = Field(description="Creation timestamp")
    
    class Config:
        orm_mode = True


# Analytics schemas
class DocumentAnalyticsEvent(BaseModel):
    """Schema for tracking document events."""
    event_type: str = Field(..., description="Type of event")
    event_data: Optional[Dict[str, Any]] = Field(None, description="Additional event data")
    session_id: Optional[str] = Field(None, description="Session identifier")


class DocumentStatsResponse(BaseModel):
    """Schema for document statistics response."""
    total_documents: int = Field(description="Total number of documents")
    total_size: int = Field(description="Total size in bytes")
    by_file_type: Dict[str, int] = Field(description="Count by file type")
    processing_status: Dict[str, int] = Field(description="Count by processing status")
    recent_uploads: int = Field(description="Recent uploads (last 7 days)")
    qa_interactions: int = Field(description="Total Q&A interactions")
    
    class Config:
        schema_extra = {
            "example": {
                "total_documents": 25,
                "total_size": 52428800,
                "by_file_type": {
                    "application/pdf": 15,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": 8,
                    "text/plain": 2
                },
                "processing_status": {
                    "completed": 23,
                    "processing": 1,
                    "failed": 1
                },
                "recent_uploads": 5,
                "qa_interactions": 127
            }
        }


# Template schemas
class DocumentTemplateCreate(BaseModel):
    """Schema for creating document templates."""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, max_length=1000, description="Template description")
    category: str = Field(..., description="Template category")
    template_content: str = Field(..., description="Template content")
    prompt_template: Optional[str] = Field(None, description="AI prompt template")
    is_public: bool = Field(False, description="Public availability")


class DocumentTemplateResponse(BaseModel):
    """Schema for document template response."""
    id: UUID = Field(description="Template ID")
    name: str = Field(description="Template name")
    description: Optional[str] = Field(description="Template description")
    category: str = Field(description="Template category")
    template_content: str = Field(description="Template content")
    prompt_template: Optional[str] = Field(description="AI prompt template")
    is_public: bool = Field(description="Public availability")
    is_system: bool = Field(description="System template")
    usage_count: int = Field(description="Usage count")
    created_at: datetime = Field(description="Creation timestamp")
    
    class Config:
        orm_mode = True


# Citation schemas
class CitationSourceResponse(BaseModel):
    """Schema for citation source response."""
    id: UUID = Field(description="Citation ID")
    title: Optional[str] = Field(description="Source title")
    authors: List[str] = Field(description="Source authors")
    publication: Optional[str] = Field(description="Publication name")
    publication_date: Optional[datetime] = Field(description="Publication date")
    doi: Optional[str] = Field(description="Digital Object Identifier")
    url: Optional[str] = Field(description="Source URL")
    apa_format: Optional[str] = Field(description="APA format citation")
    mla_format: Optional[str] = Field(description="MLA format citation")
    chicago_format: Optional[str] = Field(description="Chicago format citation")
    ieee_format: Optional[str] = Field(description="IEEE format citation")
    
    class Config:
        orm_mode = True