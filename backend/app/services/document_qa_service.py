# backend/app/services/document_qa_service.py
"""
Document Q&A service that combines RAG with Groq LLaMA3-70B for question answering.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.exceptions import DocumentQAError
from app.models.document import Document, DocumentQAInteraction
from app.schemas.document import DocumentQARequest, DocumentQAResponse, ContextSource
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import FAISSVectorStore
from app.services.simple_vector_store import SimpleVectorStore
from app.services.groq_service import get_groq_service
from app.db.repositories.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


class DocumentQAService:
    """Service for document question answering using RAG."""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        # Use simple vector store as default since FAISS has compatibility issues
        logger.info("Using simple vector store for Q&A")
        self.vector_store = SimpleVectorStore(self.embedding_service)
        self.groq_service = get_groq_service()
        
        logger.info("Initialized Document Q&A service")
    
    async def ask_question(
        self,
        document_id: UUID,
        question: str,
        user_id: UUID,
        db: Session,
        max_chunks: int = 5,
        include_sources: bool = True,
        context_window: int = 4000
    ) -> DocumentQAResponse:
        """
        Ask a question about a document using RAG.
        
        Args:
            document_id: Document ID to query
            question: User's question
            user_id: User ID asking the question
            db: Database session
            max_chunks: Maximum number of chunks to use for context
            include_sources: Whether to include source information
            context_window: Context window size in tokens
            
        Returns:
            DocumentQAResponse with answer and sources
        """
        start_time = time.time()
        
        try:
            # Get document repository
            repo = DocumentRepository(db)
            
            # Verify document exists and is processed
            document = await repo.get_document(document_id)
            if not document:
                raise DocumentQAError("Document not found")
            
            if not document.is_processed:
                raise DocumentQAError("Document is not yet processed")
            
            # Check if user has access to document
            if not await self._check_document_access(document, user_id, db):
                raise DocumentQAError("Access denied to document")
            
            # Generate embedding for the question
            question_embedding = await self.embedding_service.generate_single_embedding(question)
            
            # Search for relevant chunks
            search_results = await self.vector_store.search(
                document_id=document_id,
                query_embedding=question_embedding,
                k=max_chunks,
                threshold=0.3  # Minimum relevance threshold
            )
            
            if not search_results:
                return DocumentQAResponse(
                    answer="I couldn't find relevant information in the document to answer your question.",
                    confidence_score=0.0,
                    sources=[],
                    processing_time=time.time() - start_time,
                    document_id=document_id,
                    chunks_used=0
                )
            
            # Build context from search results
            context_chunks = []
            sources = []
            
            for result in search_results:
                context_chunks.append(result['content'])
                
                if include_sources:
                    source = ContextSource(
                        chunk_id=result['chunk_id'],
                        page_number=result['page_number'],
                        content_preview=result['content'][:150] + "..." if len(result['content']) > 150 else result['content'],
                        relevance_score=result['relevance_score']
                    )
                    sources.append(source)
            
            # Generate answer using Groq
            answer, confidence_score = await self._generate_answer(
                question=question,
                context_chunks=context_chunks,
                document_title=document.title,
                context_window=context_window
            )
            
            # Save interaction to database
            interaction = DocumentQAInteraction(
                document_id=document_id,
                user_id=user_id,
                question=question,
                answer=answer,
                confidence_score=confidence_score,
                chunks_used=len(context_chunks),
                processing_time=time.time() - start_time
            )
            
            await repo.save_qa_interaction(interaction)
            
            # Create response
            response = DocumentQAResponse(
                answer=answer,
                confidence_score=confidence_score,
                sources=sources if include_sources else [],
                processing_time=time.time() - start_time,
                document_id=document_id,
                chunks_used=len(context_chunks)
            )
            
            logger.info(f"Generated answer for document {document_id} in {response.processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error in document Q&A: {e}")
            raise DocumentQAError(f"Failed to process question: {str(e)}")
    
    async def _generate_answer(
        self,
        question: str,
        context_chunks: List[str],
        document_title: str,
        context_window: int
    ) -> Tuple[str, float]:
        """
        Generate answer using Groq LLaMA3-70B with RAG context.
        
        Args:
            question: User's question
            context_chunks: Relevant context chunks
            document_title: Document title
            context_window: Context window size in tokens
            
        Returns:
            Tuple of (answer, confidence_score)
        """
        try:
            # Build context string
            context_text = "\\n\\n".join([
                f"[Context {i+1}]\\n{chunk}" 
                for i, chunk in enumerate(context_chunks)
            ])
            
            # Create system prompt for document Q&A
            system_prompt = f"""You are an expert document analyst. Your task is to answer questions based strictly on the provided context from the document "{document_title}".

IMPORTANT GUIDELINES:
1. ONLY use information from the provided context
2. If the context doesn't contain relevant information, say so clearly
3. Be precise and concise in your answers
4. Include specific references when possible (e.g., "According to Context 1...")
5. If you're uncertain, express that uncertainty
6. Do not make up information not found in the context

CONTEXT FROM DOCUMENT:
{context_text}

Please answer the following question based ONLY on the context provided above."""
            
            # Create user message
            user_message = f"QUESTION: {question}\\n\\nPlease provide a clear, accurate answer based solely on the context provided."
            
            # Create messages for Groq
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Generate response with Groq
            response = await self.groq_service.create_chat_completion(
                messages=messages,
                temperature=0.1,  # Low temperature for factual accuracy
                max_tokens=1024,
                top_p=0.9
            )
            
            # Extract answer
            answer = response['choices'][0]['message']['content'].strip()
            
            # Calculate confidence score (simple heuristic)
            confidence_score = self._calculate_confidence_score(answer, context_chunks)
            
            return answer, confidence_score
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise DocumentQAError(f"Failed to generate answer: {str(e)}")
    
    def _calculate_confidence_score(self, answer: str, context_chunks: List[str]) -> float:
        """
        Calculate confidence score for the answer.
        
        Args:
            answer: Generated answer
            context_chunks: Context chunks used
            
        Returns:
            Confidence score between 0 and 1
        """
        try:
            # Simple heuristic based on answer characteristics
            score = 0.5  # Base score
            
            # Higher score for longer, more detailed answers
            if len(answer) > 100:
                score += 0.1
            if len(answer) > 200:
                score += 0.1
            
            # Higher score if answer references context
            if "context" in answer.lower() or "according to" in answer.lower():
                score += 0.2
            
            # Lower score for uncertainty indicators
            uncertainty_indicators = ["i'm not sure", "unclear", "uncertain", "might be", "possibly"]
            if any(indicator in answer.lower() for indicator in uncertainty_indicators):
                score -= 0.2
            
            # Lower score for "not found" type answers
            not_found_indicators = ["not found", "doesn't contain", "no information", "cannot find"]
            if any(indicator in answer.lower() for indicator in not_found_indicators):
                score -= 0.3
            
            # Higher score for more context chunks used
            if len(context_chunks) >= 3:
                score += 0.1
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5
    
    async def _check_document_access(self, document: Document, user_id: UUID, db: Session) -> bool:
        """
        Check if user has access to the document.
        
        Args:
            document: Document to check access for
            user_id: User ID to check
            db: Database session
            
        Returns:
            True if user has access, False otherwise
        """
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
            
            # Check document shares table for more detailed permissions
            repo = DocumentRepository(db)
            shares = await repo.get_document_shares(document.id)
            
            for share in shares:
                if share.shared_with_id == user_id and share.is_active and share.can_read:
                    if share.expires_at is None or share.expires_at > datetime.utcnow():
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking document access: {e}")
            return False
    
    async def get_document_summary(
        self,
        document_id: UUID,
        user_id: UUID,
        db: Session,
        summary_type: str = "comprehensive",
        max_length: int = 500
    ) -> Dict[str, Any]:
        """
        Generate a summary of the document.
        
        Args:
            document_id: Document ID
            user_id: User ID requesting summary
            db: Database session
            summary_type: Type of summary (brief, comprehensive, key_points)
            max_length: Maximum length in words
            
        Returns:
            Dictionary with summary information
        """
        try:
            repo = DocumentRepository(db)
            
            # Get document
            document = await repo.get_document(document_id)
            if not document:
                raise DocumentQAError("Document not found")
            
            # Check access
            if not await self._check_document_access(document, user_id, db):
                raise DocumentQAError("Access denied to document")
            
            # Get document chunks
            chunks, _ = await repo.get_document_chunks(document_id, 0, 50)  # Get first 50 chunks
            
            if not chunks:
                raise DocumentQAError("No content available for summary")
            
            # Combine chunk contents for summary
            content = "\\n\\n".join([chunk.content for chunk in chunks])
            
            # Generate summary using Groq
            summary = await self._generate_summary(
                content=content,
                document_title=document.title,
                summary_type=summary_type,
                max_length=max_length
            )
            
            return {
                "summary": summary,
                "summary_type": summary_type,
                "document_id": document_id,
                "key_concepts": [],  # Could be enhanced with NLP
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error generating document summary: {e}")
            raise DocumentQAError(f"Failed to generate summary: {str(e)}")
    
    async def _generate_summary(
        self,
        content: str,
        document_title: str,
        summary_type: str,
        max_length: int
    ) -> str:
        """
        Generate summary using Groq.
        
        Args:
            content: Document content
            document_title: Document title
            summary_type: Type of summary
            max_length: Maximum length in words
            
        Returns:
            Generated summary
        """
        try:
            # Create prompt based on summary type
            if summary_type == "brief":
                prompt = f"Provide a brief, 2-3 sentence summary of the following document titled '{document_title}'"
            elif summary_type == "key_points":
                prompt = f"Extract the key points from the following document titled '{document_title}' as a bulleted list"
            else:  # comprehensive
                prompt = f"Provide a comprehensive summary of the following document titled '{document_title}' in approximately {max_length} words"
            
            messages = [
                {"role": "system", "content": "You are an expert document summarizer. Provide accurate, concise summaries based on the given content."},
                {"role": "user", "content": f"{prompt}:\\n\\n{content}"}
            ]
            
            response = await self.groq_service.create_chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=min(max_length * 2, 1024)  # Rough token estimation
            )
            
            return response['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise DocumentQAError(f"Failed to generate summary: {str(e)}")
    
    async def search_document(
        self,
        document_id: UUID,
        query: str,
        user_id: UUID,
        db: Session,
        max_results: int = 10,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Search within a document for relevant passages.
        
        Args:
            document_id: Document ID
            query: Search query
            user_id: User ID
            db: Database session
            max_results: Maximum number of results
            threshold: Relevance threshold
            
        Returns:
            Search results dictionary
        """
        try:
            repo = DocumentRepository(db)
            
            # Get document
            document = await repo.get_document(document_id)
            if not document:
                raise DocumentQAError("Document not found")
            
            # Check access
            if not await self._check_document_access(document, user_id, db):
                raise DocumentQAError("Access denied to document")
            
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_single_embedding(query)
            
            # Search for relevant chunks
            search_results = await self.vector_store.search(
                document_id=document_id,
                query_embedding=query_embedding,
                k=max_results,
                threshold=threshold
            )
            
            # Format results
            passages = []
            for result in search_results:
                passages.append({
                    "content": result['content'],
                    "page_number": result['page_number'],
                    "chunk_index": result['chunk_index'],
                    "relevance_score": result['relevance_score'],
                    "preview": result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                })
            
            return {
                "query": query,
                "document_id": document_id,
                "passages": passages,
                "total_found": len(passages)
            }
            
        except Exception as e:
            logger.error(f"Error searching document: {e}")
            raise DocumentQAError(f"Failed to search document: {str(e)}")
    
    async def get_qa_history(
        self,
        document_id: UUID,
        user_id: UUID,
        db: Session,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get Q&A history for a document.
        
        Args:
            document_id: Document ID
            user_id: User ID
            db: Database session
            limit: Maximum number of interactions to return
            
        Returns:
            List of Q&A interactions
        """
        try:
            repo = DocumentRepository(db)
            
            # Get document
            document = await repo.get_document(document_id)
            if not document:
                raise DocumentQAError("Document not found")
            
            # Check access
            if not await self._check_document_access(document, user_id, db):
                raise DocumentQAError("Access denied to document")
            
            # Get Q&A interactions
            interactions = await repo.get_qa_interactions(document_id, user_id, limit)
            
            return [
                {
                    "id": str(interaction.id),
                    "question": interaction.question,
                    "answer": interaction.answer,
                    "confidence_score": interaction.confidence_score,
                    "chunks_used": interaction.chunks_used,
                    "processing_time": interaction.processing_time,
                    "user_rating": interaction.user_rating,
                    "created_at": interaction.created_at
                }
                for interaction in interactions
            ]
            
        except Exception as e:
            logger.error(f"Error getting Q&A history: {e}")
            raise DocumentQAError(f"Failed to get Q&A history: {str(e)}")
    
    async def rate_answer(
        self,
        interaction_id: UUID,
        user_id: UUID,
        rating: int,
        feedback: Optional[str],
        db: Session
    ) -> bool:
        """
        Rate a Q&A answer.
        
        Args:
            interaction_id: Interaction ID
            user_id: User ID
            rating: Rating (1-5)
            feedback: Optional feedback text
            db: Database session
            
        Returns:
            True if successful
        """
        try:
            repo = DocumentRepository(db)
            
            # Update interaction rating
            success = await repo.update_qa_interaction_rating(
                interaction_id=interaction_id,
                user_id=user_id,
                rating=rating,
                feedback=feedback
            )
            
            if success:
                logger.info(f"Updated rating for interaction {interaction_id}: {rating}/5")
            
            return success
            
        except Exception as e:
            logger.error(f"Error rating answer: {e}")
            return False