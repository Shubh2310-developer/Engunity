# backend/app/api/v1/documents.py
"""
Document management and Q&A API endpoints.
Handles file uploads, processing, and question answering.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.schemas.document import (
    DocumentCreate, DocumentResponse, DocumentUpdate, DocumentListResponse,
    DocumentQARequest, DocumentQAResponse, DocumentSummaryRequest, DocumentSummaryResponse,
    DocumentSearchRequest, DocumentSearchResponse, BulkDeleteRequest
)
from app.services.document_service import DocumentService
from app.db.repositories.document_repository import DocumentRepository
from app.agents.document_qa_agent import DocumentQAAgent
from app.core.config import settings
from app.core.exceptions import DocumentNotFoundError, InsufficientPermissionsError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Initialize services
document_service = DocumentService()
document_qa_agent = DocumentQAAgent()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process a document for Q&A.
    
    - **file**: Document file (PDF, DOCX, TXT)
    - **title**: Optional custom title
    - **description**: Optional description
    - **tags**: Optional comma-separated tags
    """
    try:
        # Validate file type
        allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: PDF, DOCX, TXT"
            )
        
        # Check file size
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Check user's document limit
        repo = DocumentRepository(db)
        user_doc_count = await repo.count_user_documents(current_user.id)
        
        if user_doc_count >= settings.MAX_DOCUMENTS_PER_USER:
            raise HTTPException(
                status_code=400,
                detail=f"Document limit reached. Maximum: {settings.MAX_DOCUMENTS_PER_USER}"
            )
        
        # Process tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Create document record
        document_data = DocumentCreate(
            title=title or file.filename,
            description=description,
            filename=file.filename,
            file_type=file.content_type,
            file_size=file.size,
            tags=tag_list
        )
        
        # Upload and process document
        document = await document_service.upload_document(
            file=file,
            document_data=document_data,
            user_id=current_user.id,
            db=db
        )
        
        # Start background processing
        background_tasks.add_task(
            document_service.process_document_content,
            document.id,
            db
        )
        
        logger.info(f"Document uploaded: {document.id} by user {current_user.id}")
        
        return DocumentResponse.from_orm(document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None),
    sort_by: str = Query("created_at", regex="^(created_at|title|file_size|updated_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List user's documents with filtering and pagination.
    
    - **skip**: Number of documents to skip
    - **limit**: Maximum number of documents to return
    - **search**: Search in title and description
    - **tags**: Filter by tags (comma-separated)
    - **file_type**: Filter by file type
    - **sort_by**: Sort field
    - **sort_order**: Sort order (asc/desc)
    """
    try:
        repo = DocumentRepository(db)
        
        # Parse tags filter
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Get documents
        documents, total = await repo.list_user_documents(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            search=search,
            tags=tag_list,
            file_type=file_type,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return DocumentListResponse(
            documents=[DocumentResponse.from_orm(doc) for doc in documents],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific document by ID."""
    try:
        repo = DocumentRepository(db)
        document = await repo.get_user_document(document_id, current_user.id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse.from_orm(document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document")


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    document_update: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update document metadata."""
    try:
        repo = DocumentRepository(db)
        document = await repo.get_user_document(document_id, current_user.id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        updated_document = await repo.update_document(document_id, document_update)
        
        logger.info(f"Document updated: {document_id} by user {current_user.id}")
        
        return DocumentResponse.from_orm(updated_document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document: {e}")
        raise HTTPException(status_code=500, detail="Failed to update document")


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document and all associated data."""
    try:
        repo = DocumentRepository(db)
        document = await repo.get_user_document(document_id, current_user.id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete document and cleanup files
        await document_service.delete_document(document_id, db)
        
        logger.info(f"Document deleted: {document_id} by user {current_user.id}")
        
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
    """Delete multiple documents at once."""
    try:
        repo = DocumentRepository(db)
        
        # Verify all documents belong to user
        for doc_id in request.document_ids:
            document = await repo.get_user_document(doc_id, current_user.id)
            if not document:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Document {doc_id} not found"
                )
        
        # Delete all documents
        deleted_count = 0
        for doc_id in request.document_ids:
            try:
                await document_service.delete_document(doc_id, db)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting document {doc_id}: {e}")
        
        logger.info(f"Bulk deleted {deleted_count} documents by user {current_user.id}")
        
        return {
            "message": f"Successfully deleted {deleted_count} documents",
            "deleted_count": deleted_count,
            "total_requested": len(request.document_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete documents")


@router.post("/{document_id}/ask", response_model=DocumentQAResponse)
async def ask_question(
    document_id: UUID,
    request: DocumentQARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ask a question about a specific document.
    Uses RAG to provide context-aware answers.
    """
    try:
        repo = DocumentRepository(db)
        document = await repo.get_user_document(document_id, current_user.id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.processing_status != "completed":
            raise HTTPException(
                status_code=400, 
                detail="Document is still processing. Please try again later."
            )
        
        # Get document vector store
        vector_store = await document_service.get_document_vector_store(document_id)
        
        if not vector_store:
            raise HTTPException(
                status_code=500,
                detail="Document vector store not available"
            )
        
        # Answer question using agent
        response = await document_qa_agent.answer_question(
            request=request,
            document=document,
            vector_store=vector_store
        )
        
        # Log the interaction
        await repo.log_qa_interaction(
            document_id=document_id,
            user_id=current_user.id,
            question=request.question,
            answer=response.answer,
            confidence_score=response.confidence_score
        )
        
        logger.info(f"Q&A interaction: document {document_id}, user {current_user.id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail="Failed to answer question")


@router.post("/{document_id}/ask/stream")
async def ask_question_stream(
    document_id: UUID,
    request: DocumentQARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ask a question with streaming response.
    Returns Server-Sent Events for real-time answers.
    """
    try:
        repo = DocumentRepository(db)
        document = await repo.get_user_document(document_id, current_user.id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.processing_status != "completed":
            raise HTTPException(
                status_code=400, 
                detail="Document is still processing"
            )
        
        # Set streaming in request
        request.stream = True
        
        async def generate_response():
            try:
                vector_store = await document_service.get_document_vector_store(document_id)
                
                # Get relevant context
                relevant_docs = vector_store.similarity_search_with_score(
                    request.question, k=request.max_chunks or 5
                )
                
                context = "\n\n".join([doc.page_content for doc, _ in relevant_docs])
                
                # Stream the response
                async for chunk in document_qa_agent.ai_service.stream_completion(
                    f"Based on this context: {context}\n\nQuestion: {request.question}\n\nAnswer:"
                ):
                    yield f"data: {chunk}\n\n"
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Error in streaming response: {e}")
                yield f"data: Error: {str(e)}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in streaming Q&A: {e}")
        raise HTTPException(status_code=500, detail="Failed to stream response")


@router.post("/{document_id}/summarize", response_model=DocumentSummaryResponse)
async def summarize_document(
    document_id: UUID,
    request: DocumentSummaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a summary of the document."""
    try:
        repo = DocumentRepository(db)
        document = await repo.get_user_document(document_id, current_user.id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.processing_status != "completed":
            raise HTTPException(
                status_code=400,
                detail="Document is still processing"
            )
        
        vector_store = await document_service.get_document_vector_store(document_id)
        
        summary = await document_qa_agent.summarize_document(
            document=document,
            vector_store=vector_store,
            summary_type=request.summary_type
        )
        
        # Extract key concepts
        key_concepts = await document_qa_agent.extract_key_concepts(
            document=document,
            vector_store=vector_store
        )
        
        response = DocumentSummaryResponse(
            summary=summary,
            summary_type=request.summary_type,
            document_id=document_id,
            key_concepts=key_concepts,
            generated_at=datetime.utcnow()
        )
        
        logger.info(f"Document summarized: {document_id} by user {current_user.id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error summarizing document: {e}")
        raise HTTPException(status_code=500, detail="Failed to summarize document")


@router.post("/{document_id}/search", response_model=DocumentSearchResponse)
async def search_document(
    document_id: UUID,
    request: DocumentSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for specific content within a document."""
    try:
        repo = DocumentRepository(db)
        document = await repo.get_user_document(document_id, current_user.id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.processing_status != "completed":
            raise HTTPException(
                status_code=400,
                detail="Document is still processing"
            )
        
        vector_store = await document_service.get_document_vector_store(document_id)
        
        # Find related passages
        passages = await document_qa_agent.find_related_passages(
            document=document,
            vector_store=vector_store,
            query=request.query,
            max_passages=request.max_results or 10
        )
        
        response = DocumentSearchResponse(
            query=request.query,
            document_id=document_id,
            passages=passages,
            total_found=len(passages)
        )
        
        logger.info(f"Document searched: {document_id} by user {current_user.id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching document: {e}")
        raise HTTPException(status_code=500, detail="Failed to search document")


@router.get("/{document_id}/status")
async def get_processing_status(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the processing status of a document."""
    try:
        repo = DocumentRepository(db)
        document = await repo.get_user_document(document_id, current_user.id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "document_id": document_id,
            "processing_status": document.processing_status,
            "error_message": document.error_message,
            "processed_at": document.processed_at,
            "chunk_count": document.chunk_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reprocess a document (e.g., after processing failure)."""
    try:
        repo = DocumentRepository(db)
        document = await repo.get_user_document(document_id, current_user.id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Reset processing status
        await repo.update_processing_status(document_id, "processing", None)
        
        # Start background reprocessing
        background_tasks.add_task(
            document_service.process_document_content,
            document_id,
            db
        )
        
        logger.info(f"Document reprocessing started: {document_id} by user {current_user.id}")
        
        return {"message": "Document reprocessing started"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reprocessing document: {e}")
        raise HTTPException(status_code=500, detail="Failed to reprocess document")


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download the original document file."""
    try:
        repo = DocumentRepository(db)
        document = await repo.get_user_document(document_id, current_user.id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get file from storage
        file_stream = await document_service.download_document_file(document_id)
        
        return StreamingResponse(
            file_stream,
            media_type=document.file_type,
            headers={
                "Content-Disposition": f"attachment; filename={document.filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document: {e}")
        raise HTTPException(status_code=500, detail="Failed to download document")


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document chunks for preview/debugging."""
    try:
        repo = DocumentRepository(db)
        document = await repo.get_user_document(document_id, current_user.id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        skip = (page - 1) * limit
        chunks, total = await repo.get_document_chunks(document_id, skip, limit)
        
        return {
            "chunks": [
                {
                    "id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "content": chunk.content,
                    "token_count": chunk.token_count
                }
                for chunk in chunks
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document chunks: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chunks")


@router.get("/stats/user")
async def get_user_document_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's document statistics."""
    try:
        repo = DocumentRepository(db)
        stats = await repo.get_user_document_stats(current_user.id)
        
        return {
            "total_documents": stats.get("total_documents", 0),
            "total_size": stats.get("total_size", 0),
            "by_file_type": stats.get("by_file_type", {}),
            "processing_status": stats.get("processing_status", {}),
            "recent_uploads": stats.get("recent_uploads", 0),
            "qa_interactions": stats.get("qa_interactions", 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")