# backend/app/api/v1/document_qa.py
"""
Document Q&A API endpoints for RAG-based question answering.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user
from app.core.exceptions import DocumentQAError, DocumentProcessingError
from app.models.user import User
from app.schemas.document import (
    DocumentCreate, DocumentResponse, DocumentQARequest, DocumentQAResponse,
    DocumentSummaryRequest, DocumentSummaryResponse, DocumentSearchRequest,
    DocumentSearchResponse, DocumentListResponse, BulkDeleteRequest
)
from app.services.document_service import DocumentService
from app.services.document_qa_service import DocumentQAService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import FAISSVectorStore
from app.db.repositories.document_repository import DocumentRepository
from app.models.document import Document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Document Q&A"])

# Initialize services
document_service = DocumentService()
qa_service = DocumentQAService()
embedding_service = EmbeddingService()
vector_store = FAISSVectorStore(embedding_service)


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: UUID
    message: str
    processing_status: str


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document for Q&A processing.
    
    Supports PDF, DOCX, TXT, and MD files.
    """
    try:
        # Validate file type
        allowed_types = {
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'text/plain': 'txt',
            'text/markdown': 'md'
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Supported types: PDF, DOCX, TXT, MD"
            )
        
        # Check file size
        file_size = 0
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 10MB limit"
            )
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Create document data
        document_data = DocumentCreate(
            title=title,
            description=description,
            tags=tag_list,
            filename=file.filename,
            file_type=file.content_type,
            file_size=file_size
        )
        
        # Reset file pointer
        await file.seek(0)
        
        # Upload document (using anonymous user ID since no auth required)
        # Using a fixed UUID for anonymous user
        from uuid import UUID
        anonymous_user_id = UUID("00000000-0000-0000-0000-000000000001")
        document = await document_service.upload_document(
            file=file.file,
            document_data=document_data,
            user_id=anonymous_user_id,
            db=db
        )
        
        # Process document in background
        background_tasks.add_task(
            process_document_background,
            document.id,
            db
        )
        
        return DocumentUploadResponse(
            document_id=document.id,
            message="Document uploaded successfully. Processing will begin shortly.",
            processing_status="pending"
        )
        
    except DocumentProcessingError as e:
        logger.error(f"Document processing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")


async def process_document_background(document_id: UUID, db: Session):
    """Background task to process document."""
    try:
        await document_service.process_document_content(document_id, db)
        logger.info(f"Successfully processed document {document_id}")
    except Exception as e:
        logger.error(f"Background processing failed for document {document_id}: {e}")


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List user's documents with optional filtering.
    """
    try:
        repo = DocumentRepository(db)
        
        # Get all documents (no user filter since no auth required)
        # Use a query to get all documents
        query = db.query(Document)
        
        if status:
            query = query.filter(Document.processing_status == status)
        
        total = query.count()
        documents = query.offset(skip).limit(limit).all()
        
        return DocumentListResponse(
            documents=[DocumentResponse.from_orm(doc) for doc in documents],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get document details.
    """
    try:
        repo = DocumentRepository(db)
        document = await repo.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # No access check needed since authentication is removed
        return DocumentResponse.from_orm(document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document")


@router.post("/{document_id}/ask", response_model=DocumentQAResponse)
async def ask_question(
    document_id: UUID,
    request: DocumentQARequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question about a document using RAG.
    """
    try:
        from uuid import UUID
        anonymous_user_id = UUID("00000000-0000-0000-0000-000000000001")
        response = await qa_service.ask_question(
            document_id=document_id,
            question=request.question,
            user_id=anonymous_user_id,
            db=db,
            max_chunks=request.max_chunks,
            include_sources=request.include_sources,
            context_window=request.context_window
        )
        
        return response
        
    except DocumentQAError as e:
        logger.error(f"Document Q&A error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error asking question: {e}")
        raise HTTPException(status_code=500, detail="Failed to process question")


@router.post("/{document_id}/summarize", response_model=DocumentSummaryResponse)
async def summarize_document(
    document_id: UUID,
    request: DocumentSummaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a summary of the document.
    """
    try:
        summary_data = await qa_service.get_document_summary(
            document_id=document_id,
            user_id=current_user.id,
            db=db,
            summary_type=request.summary_type,
            max_length=request.max_length
        )
        
        return DocumentSummaryResponse(**summary_data)
        
    except DocumentQAError as e:
        logger.error(f"Document summary error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")


@router.post("/{document_id}/search", response_model=DocumentSearchResponse)
async def search_document(
    document_id: UUID,
    request: DocumentSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search within a document for relevant passages.
    """
    try:
        search_results = await qa_service.search_document(
            document_id=document_id,
            query=request.query,
            user_id=current_user.id,
            db=db,
            max_results=request.max_results,
            threshold=request.threshold
        )
        
        return DocumentSearchResponse(**search_results)
        
    except DocumentQAError as e:
        logger.error(f"Document search error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching document: {e}")
        raise HTTPException(status_code=500, detail="Failed to search document")


@router.get("/{document_id}/qa-history")
async def get_qa_history(
    document_id: UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Q&A history for a document.
    """
    try:
        history = await qa_service.get_qa_history(
            document_id=document_id,
            user_id=current_user.id,
            db=db,
            limit=limit
        )
        
        return {"interactions": history}
        
    except DocumentQAError as e:
        logger.error(f"Q&A history error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting Q&A history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Q&A history")


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reprocess a document (regenerate embeddings).
    """
    try:
        repo = DocumentRepository(db)
        document = await repo.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check ownership
        if document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Reprocess in background
        background_tasks.add_task(
            reprocess_document_background,
            document_id,
            db
        )
        
        return {"message": "Document reprocessing started"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reprocessing document: {e}")
        raise HTTPException(status_code=500, detail="Failed to reprocess document")


async def reprocess_document_background(document_id: UUID, db: Session):
    """Background task to reprocess document."""
    try:
        await document_service.reindex_document(document_id, db)
        logger.info(f"Successfully reprocessed document {document_id}")
    except Exception as e:
        logger.error(f"Background reprocessing failed for document {document_id}: {e}")


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a document and all associated data.
    """
    try:
        repo = DocumentRepository(db)
        document = await repo.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Skip ownership check since no auth required
        
        # Delete document
        await document_service.delete_document(document_id, db)
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.post("/bulk-delete")
async def bulk_delete_documents(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete multiple documents.
    """
    try:
        repo = DocumentRepository(db)
        results = {"deleted": [], "failed": []}
        
        for document_id in request.document_ids:
            try:
                document = await repo.get_document(document_id)
                
                if not document:
                    results["failed"].append({"id": str(document_id), "error": "Document not found"})
                    continue
                
                # Check ownership
                if document.user_id != current_user.id:
                    results["failed"].append({"id": str(document_id), "error": "Access denied"})
                    continue
                
                # Delete document
                await document_service.delete_document(document_id, db)
                results["deleted"].append(str(document_id))
                
            except Exception as e:
                results["failed"].append({"id": str(document_id), "error": str(e)})
        
        return results
        
    except Exception as e:
        logger.error(f"Error bulk deleting documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete documents")


@router.get("/{document_id}/stats")
async def get_document_stats(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get document statistics.
    """
    try:
        repo = DocumentRepository(db)
        document = await repo.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check access
        if not await _check_document_access(document, current_user.id, db):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get statistics
        stats = await document_service.get_document_statistics(document_id)
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document statistics")


@router.post("/qa-interactions/{interaction_id}/rate")
async def rate_qa_interaction(
    interaction_id: UUID,
    rating: int,
    feedback: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rate a Q&A interaction.
    """
    try:
        if rating < 1 or rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        success = await qa_service.rate_answer(
            interaction_id=interaction_id,
            user_id=current_user.id,
            rating=rating,
            feedback=feedback,
            db=db
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to rate interaction")
        
        return {"message": "Rating submitted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rating interaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to rate interaction")


@router.get("/system/health")
async def system_health():
    """
    Check system health for document Q&A services.
    """
    try:
        # Check embedding service
        embedding_info = await embedding_service.get_model_info()
        
        # Check vector store
        vector_stats = await vector_store.get_all_index_stats()
        
        return {
            "status": "healthy",
            "embedding_service": embedding_info,
            "vector_store": vector_stats,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }


async def _check_document_access(document, user_id: UUID, db: Session) -> bool:
    """Helper function to check document access."""
    try:
        # Owner has access
        if document.user_id == user_id:
            return True
        
        # Check if document is public
        if document.is_public:
            return True
        
        # Check if document is shared with user
        if user_id in document.shared_with:
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking document access: {e}")
        return False