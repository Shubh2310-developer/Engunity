# backend/app/db/repositories/document_repository.py
"""
Database repository for document operations.
Handles all database interactions for documents, chunks, and related entities.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.models.document import (
    Document, DocumentChunk, DocumentQAInteraction, DocumentShare, 
    DocumentFolder, DocumentFolderItem, DocumentTemplate, DocumentAnalytics,
    CitationSource
)
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class DocumentRepository:
    """Repository class for document-related database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_document(
        self, 
        document_data: DocumentCreate, 
        user_id: UUID, 
        file_path: str
    ) -> Document:
        """
        Create a new document record.
        
        Args:
            document_data: Document creation data
            user_id: ID of the document owner
            file_path: Path to the uploaded file
            
        Returns:
            Created document instance
        """
        try:
            document = Document(
                title=document_data.title,
                description=document_data.description,
                filename=document_data.filename,
                file_type=document_data.file_type,
                file_size=document_data.file_size,
                file_path=file_path,
                user_id=user_id,
                tags=document_data.tags or [],
                language=document_data.language or "en",
                is_public=document_data.is_public or False,
                processing_status="pending"
            )
            
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"Created document: {document.id}")
            return document
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating document: {e}")
            raise DatabaseError(f"Failed to create document: {str(e)}")
    
    async def get_document(self, document_id: UUID) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document instance or None if not found
        """
        try:
            return self.db.query(Document).filter(Document.id == document_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting document {document_id}: {e}")
            raise DatabaseError(f"Failed to get document: {str(e)}")
    
    async def get_user_document(self, document_id: UUID, user_id: UUID) -> Optional[Document]:
        """
        Get a document by ID that belongs to a specific user.
        
        Args:
            document_id: Document ID
            user_id: User ID
            
        Returns:
            Document instance or None if not found/accessible
        """
        try:
            return self.db.query(Document).filter(
                and_(
                    Document.id == document_id,
                    or_(
                        Document.user_id == user_id,
                        Document.is_public == True,
                        Document.shared_with.contains([user_id])
                    )
                )
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user document: {e}")
            raise DatabaseError(f"Failed to get document: {str(e)}")
    
    async def list_user_documents(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        file_type: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Document], int]:
        """
        List documents for a user with filtering and pagination.
        
        Args:
            user_id: User ID
            skip: Number of documents to skip
            limit: Maximum documents to return
            search: Search term for title/description
            tags: Filter by tags
            file_type: Filter by file type
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            Tuple of (documents list, total count)
        """
        try:
            # Base query
            query = self.db.query(Document).filter(
                or_(
                    Document.user_id == user_id,
                    Document.is_public == True,
                    Document.shared_with.contains([user_id])
                )
            )
            
            # Apply filters
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Document.title.ilike(search_term),
                        Document.description.ilike(search_term)
                    )
                )
            
            if tags:
                for tag in tags:
                    query = query.filter(Document.tags.contains([tag]))
            
            if file_type:
                query = query.filter(Document.file_type == file_type)
            
            # Get total count before pagination
            total = query.count()
            
            # Apply sorting
            sort_column = getattr(Document, sort_by, Document.created_at)
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Apply pagination
            documents = query.offset(skip).limit(limit).all()
            
            return documents, total
            
        except SQLAlchemyError as e:
            logger.error(f"Error listing user documents: {e}")
            raise DatabaseError(f"Failed to list documents: {str(e)}")
    
    async def update_document(
        self, 
        document_id: UUID, 
        document_update: DocumentUpdate
    ) -> Optional[Document]:
        """
        Update document metadata.
        
        Args:
            document_id: Document ID
            document_update: Update data
            
        Returns:
            Updated document instance
        """
        try:
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return None
            
            # Update fields
            update_data = document_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(document, field, value)
            
            document.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"Updated document: {document_id}")
            return document
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating document: {e}")
            raise DatabaseError(f"Failed to update document: {str(e)}")
    
    async def delete_document(self, document_id: UUID) -> bool:
        """
        Delete a document and all related data.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return False
            
            # Delete related data (cascading should handle this, but being explicit)
            self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
            self.db.query(DocumentQAInteraction).filter(DocumentQAInteraction.document_id == document_id).delete()
            self.db.query(DocumentShare).filter(DocumentShare.document_id == document_id).delete()
            self.db.query(DocumentAnalytics).filter(DocumentAnalytics.document_id == document_id).delete()
            self.db.query(CitationSource).filter(CitationSource.document_id == document_id).delete()
            
            # Delete the document
            self.db.delete(document)
            self.db.commit()
            
            logger.info(f"Deleted document: {document_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting document: {e}")
            raise DatabaseError(f"Failed to delete document: {str(e)}")
    
    async def update_processing_status(
        self,
        document_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        chunk_count: Optional[int] = None
    ) -> None:
        """
        Update document processing status.
        
        Args:
            document_id: Document ID
            status: New processing status
            error_message: Error message if failed
            chunk_count: Number of chunks created
        """
        try:
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise DatabaseError("Document not found")
            
            document.processing_status = status
            if error_message:
                document.error_message = error_message
            if chunk_count is not None:
                document.chunk_count = chunk_count
            if status == "completed":
                document.processed_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Updated processing status for document {document_id}: {status}")
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating processing status: {e}")
            raise DatabaseError(f"Failed to update processing status: {str(e)}")
    
    async def save_document_chunks(self, chunks: List[DocumentChunk]) -> None:
        """
        Save document chunks to database.
        
        Args:
            chunks: List of document chunks
        """
        try:
            self.db.add_all(chunks)
            self.db.commit()
            
            logger.info(f"Saved {len(chunks)} chunks")
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error saving chunks: {e}")
            raise DatabaseError(f"Failed to save chunks: {str(e)}")
    
    async def get_document_chunks(
        self, 
        document_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[DocumentChunk], int]:
        """
        Get chunks for a document with pagination.
        
        Args:
            document_id: Document ID
            skip: Number of chunks to skip
            limit: Maximum chunks to return
            
        Returns:
            Tuple of (chunks list, total count)
        """
        try:
            query = self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index)
            
            total = query.count()
            chunks = query.offset(skip).limit(limit).all()
            
            return chunks, total
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting document chunks: {e}")
            raise DatabaseError(f"Failed to get chunks: {str(e)}")
    
    async def log_qa_interaction(
        self,
        document_id: UUID,
        user_id: UUID,
        question: str,
        answer: str,
        confidence_score: Optional[float] = None,
        chunks_used: Optional[int] = None,
        processing_time: Optional[float] = None
    ) -> DocumentQAInteraction:
        """
        Log a Q&A interaction.
        
        Args:
            document_id: Document ID
            user_id: User ID
            question: Question asked
            answer: Generated answer
            confidence_score: Confidence score
            chunks_used: Number of chunks used
            processing_time: Processing time in seconds
            
        Returns:
            Created interaction record
        """
        try:
            interaction = DocumentQAInteraction(
                document_id=document_id,
                user_id=user_id,
                question=question,
                answer=answer,
                confidence_score=confidence_score,
                chunks_used=chunks_used,
                processing_time=processing_time
            )
            
            self.db.add(interaction)
            self.db.commit()
            self.db.refresh(interaction)
            
            logger.info(f"Logged Q&A interaction for document {document_id}")
            return interaction
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error logging Q&A interaction: {e}")
            raise DatabaseError(f"Failed to log interaction: {str(e)}")
    
    async def save_qa_interaction(self, interaction: DocumentQAInteraction) -> None:
        """
        Save a Q&A interaction (alias for compatibility).
        
        Args:
            interaction: DocumentQAInteraction instance
        """
        try:
            self.db.add(interaction)
            self.db.commit()
            self.db.refresh(interaction)
            
            logger.info(f"Saved Q&A interaction for document {interaction.document_id}")
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error saving Q&A interaction: {e}")
            raise DatabaseError(f"Failed to save interaction: {str(e)}")
    
    async def get_user_document_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get document statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Total documents
            total_docs = self.db.query(Document).filter(Document.user_id == user_id).count()
            
            # Total size
            total_size = self.db.query(func.sum(Document.file_size)).filter(
                Document.user_id == user_id
            ).scalar() or 0
            
            # By file type
            file_type_stats = self.db.query(
                Document.file_type, 
                func.count(Document.id)
            ).filter(Document.user_id == user_id).group_by(Document.file_type).all()
            
            by_file_type = {file_type: count for file_type, count in file_type_stats}
            
            # By processing status
            status_stats = self.db.query(
                Document.processing_status,
                func.count(Document.id)
            ).filter(Document.user_id == user_id).group_by(Document.processing_status).all()
            
            processing_status = {status: count for status, count in status_stats}
            
            # Recent uploads (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_uploads = self.db.query(Document).filter(
                and_(
                    Document.user_id == user_id,
                    Document.created_at >= week_ago
                )
            ).count()
            
            # Q&A interactions
            qa_interactions = self.db.query(DocumentQAInteraction).join(Document).filter(
                Document.user_id == user_id
            ).count()
            
            return {
                "total_documents": total_docs,
                "total_size": total_size,
                "by_file_type": by_file_type,
                "processing_status": processing_status,
                "recent_uploads": recent_uploads,
                "qa_interactions": qa_interactions
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting user stats: {e}")
            raise DatabaseError(f"Failed to get statistics: {str(e)}")
    
    async def count_user_documents(self, user_id: UUID) -> int:
        """
        Count total documents for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Document count
        """
        try:
            return self.db.query(Document).filter(Document.user_id == user_id).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting user documents: {e}")
            raise DatabaseError(f"Failed to count documents: {str(e)}")
    
    # Folder operations
    async def create_folder(
        self, 
        name: str, 
        user_id: UUID, 
        parent_id: Optional[UUID] = None,
        description: Optional[str] = None,
        color: Optional[str] = None
    ) -> DocumentFolder:
        """Create a document folder."""
        try:
            folder = DocumentFolder(
                name=name,
                description=description,
                color=color,
                parent_id=parent_id,
                user_id=user_id
            )
            
            self.db.add(folder)
            self.db.commit()
            self.db.refresh(folder)
            
            logger.info(f"Created folder: {folder.id}")
            return folder
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating folder: {e}")
            raise DatabaseError(f"Failed to create folder: {str(e)}")
    
    async def add_document_to_folder(
        self, 
        document_id: UUID, 
        folder_id: UUID
    ) -> DocumentFolderItem:
        """Add a document to a folder."""
        try:
            # Check if already exists
            existing = self.db.query(DocumentFolderItem).filter(
                and_(
                    DocumentFolderItem.document_id == document_id,
                    DocumentFolderItem.folder_id == folder_id
                )
            ).first()
            
            if existing:
                return existing
            
            folder_item = DocumentFolderItem(
                document_id=document_id,
                folder_id=folder_id
            )
            
            self.db.add(folder_item)
            self.db.commit()
            self.db.refresh(folder_item)
            
            return folder_item
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error adding document to folder: {e}")
            raise DatabaseError(f"Failed to add document to folder: {str(e)}")
    
    # Sharing operations
    async def share_document(
        self,
        document_id: UUID,
        owner_id: UUID,
        shared_with_id: UUID,
        permissions: Dict[str, bool],
        share_message: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> DocumentShare:
        """Share a document with another user."""
        try:
            share = DocumentShare(
                document_id=document_id,
                owner_id=owner_id,
                shared_with_id=shared_with_id,
                can_read=permissions.get("can_read", True),
                can_ask_questions=permissions.get("can_ask_questions", True),
                can_edit=permissions.get("can_edit", False),
                can_delete=permissions.get("can_delete", False),
                share_message=share_message,
                expires_at=expires_at
            )
            
            self.db.add(share)
            self.db.commit()
            self.db.refresh(share)
            
            logger.info(f"Shared document {document_id} with user {shared_with_id}")
            return share
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error sharing document: {e}")
            raise DatabaseError(f"Failed to share document: {str(e)}")
    
    # Analytics operations
    async def log_document_event(
        self,
        document_id: UUID,
        user_id: UUID,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> DocumentAnalytics:
        """Log a document analytics event."""
        try:
            analytics = DocumentAnalytics(
                document_id=document_id,
                user_id=user_id,
                event_type=event_type,
                event_data=event_data,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id
            )
            
            self.db.add(analytics)
            self.db.commit()
            self.db.refresh(analytics)
            
            return analytics
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error logging analytics event: {e}")
            raise DatabaseError(f"Failed to log event: {str(e)}")
    
    # Citation operations
    async def save_citation_sources(
        self, 
        document_id: UUID, 
        citations: List[Dict[str, Any]]
    ) -> List[CitationSource]:
        """Save extracted citation sources."""
        try:
            citation_objects = []
            for citation_data in citations:
                citation = CitationSource(
                    document_id=document_id,
                    **citation_data
                )
                citation_objects.append(citation)
            
            self.db.add_all(citation_objects)
            self.db.commit()
            
            for citation in citation_objects:
                self.db.refresh(citation)
            
            logger.info(f"Saved {len(citation_objects)} citations for document {document_id}")
            return citation_objects
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error saving citations: {e}")
            raise DatabaseError(f"Failed to save citations: {str(e)}")
    
    async def get_document_citations(self, document_id: UUID) -> List[CitationSource]:
        """Get citation sources for a document."""
        try:
            return self.db.query(CitationSource).filter(
                CitationSource.document_id == document_id
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting citations: {e}")
            raise DatabaseError(f"Failed to get citations: {str(e)}")