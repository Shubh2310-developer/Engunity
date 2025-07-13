# backend/app/agents/document_qa_agent.py
"""
Document Q&A Agent using LangChain for intelligent document question answering.
Implements RAG (Retrieval Augmented Generation) with FAISS vector store.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from langchain.agents import initialize_agent, AgentType
from langchain.tools import BaseTool
from langchain.schema import Document as LangChainDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.llms.base import LLM
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from pydantic import BaseModel

from app.services.ai_service import AIService
from app.core.config import settings
from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentQARequest, DocumentQAResponse, ContextSource

logger = logging.getLogger(__name__)


class DocumentSearchTool(BaseTool):
    """Tool for searching relevant document chunks."""
    
    name = "document_search"
    description = "Search for relevant information in uploaded documents"
    vector_store: FAISS
    document_id: str
    
    def __init__(self, vector_store: FAISS, document_id: str):
        super().__init__()
        self.vector_store = vector_store
        self.document_id = document_id
    
    def _run(self, query: str) -> str:
        """Search for relevant document chunks."""
        try:
            # Search for top-k relevant chunks
            docs = self.vector_store.similarity_search_with_score(
                query, k=settings.RAG_TOP_K
            )
            
            results = []
            for doc, score in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "relevance_score": float(score)
                })
            
            return str(results)
        except Exception as e:
            logger.error(f"Error in document search: {e}")
            return "Error searching documents"
    
    async def _arun(self, query: str) -> str:
        """Async version of document search."""
        return self._run(query)


class DocumentQAAgent:
    """
    Advanced document Q&A agent that uses RAG to answer questions
    based on uploaded documents.
    """
    
    def __init__(self):
        self.ai_service = AIService()
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL_NAME
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=5,  # Remember last 5 exchanges
            return_messages=True
        )
        
        # Custom prompt template for document Q&A
        self.qa_prompt = PromptTemplate(
            input_variables=["context", "question", "chat_history"],
            template="""
You are an intelligent document analysis assistant. Your task is to answer questions based on the provided document context.

Context from documents:
{context}

Previous conversation:
{chat_history}

Question: {question}

Instructions:
1. Answer based ONLY on the provided context
2. If the answer is not in the context, say "I cannot find this information in the provided documents"
3. Cite specific parts of the documents when possible
4. Be concise but comprehensive
5. If multiple documents contain relevant information, synthesize the information

Answer:"""
        )
    
    async def process_document_chunks(
        self, 
        document: Document, 
        chunks: List[DocumentChunk]
    ) -> FAISS:
        """
        Process document chunks and create/update vector store.
        
        Args:
            document: Document model instance
            chunks: List of document chunks
            
        Returns:
            FAISS vector store
        """
        try:
            # Convert chunks to LangChain documents
            langchain_docs = []
            for chunk in chunks:
                metadata = {
                    "document_id": str(document.id),
                    "document_title": document.title,
                    "chunk_id": str(chunk.id),
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "file_type": document.file_type
                }
                
                langchain_docs.append(
                    LangChainDocument(
                        page_content=chunk.content,
                        metadata=metadata
                    )
                )
            
            # Create vector store
            vector_store = FAISS.from_documents(langchain_docs, self.embeddings)
            
            logger.info(f"Created vector store for document {document.id} with {len(chunks)} chunks")
            return vector_store
            
        except Exception as e:
            logger.error(f"Error processing document chunks: {e}")
            raise
    
    async def answer_question(
        self,
        request: DocumentQARequest,
        document: Document,
        vector_store: FAISS
    ) -> DocumentQAResponse:
        """
        Answer a question based on document content using RAG.
        
        Args:
            request: Q&A request with question and options
            document: Document model instance
            vector_store: FAISS vector store for the document
            
        Returns:
            DocumentQAResponse with answer and sources
        """
        try:
            start_time = datetime.utcnow()
            
            # Search for relevant document chunks
            relevant_docs = vector_store.similarity_search_with_score(
                request.question, 
                k=request.max_chunks or settings.RAG_TOP_K
            )
            
            if not relevant_docs:
                return DocumentQAResponse(
                    answer="I cannot find relevant information in this document to answer your question.",
                    confidence_score=0.0,
                    sources=[],
                    processing_time=(datetime.utcnow() - start_time).total_seconds(),
                    document_id=document.id
                )
            
            # Prepare context from relevant chunks
            context_parts = []
            sources = []
            
            for doc, score in relevant_docs:
                context_parts.append(f"[Page {doc.metadata.get('page_number', 'N/A')}]: {doc.page_content}")
                
                sources.append(ContextSource(
                    chunk_id=doc.metadata.get('chunk_id'),
                    page_number=doc.metadata.get('page_number'),
                    content_preview=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    relevance_score=float(score)
                ))
            
            context = "\n\n".join(context_parts)
            
            # Get chat history for context
            chat_history = ""
            if hasattr(self.memory, 'chat_memory') and self.memory.chat_memory.messages:
                chat_history = "\n".join([
                    f"Human: {msg.content}" if msg.type == "human" else f"Assistant: {msg.content}"
                    for msg in self.memory.chat_memory.messages[-4:]  # Last 2 exchanges
                ])
            
            # Generate answer using AI service
            prompt = self.qa_prompt.format(
                context=context,
                question=request.question,
                chat_history=chat_history
            )
            
            # Use streaming if requested
            if request.stream:
                answer = ""
                async for chunk in self.ai_service.stream_completion(prompt):
                    answer += chunk
            else:
                answer = await self.ai_service.generate_completion(prompt)
            
            # Calculate confidence score based on relevance scores
            avg_relevance = sum(score for _, score in relevant_docs) / len(relevant_docs)
            confidence_score = max(0.0, min(1.0, (1.0 - avg_relevance) * 0.8 + 0.2))
            
            # Update conversation memory
            self.memory.chat_memory.add_user_message(request.question)
            self.memory.chat_memory.add_ai_message(answer)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return DocumentQAResponse(
                answer=answer,
                confidence_score=confidence_score,
                sources=sources,
                processing_time=processing_time,
                document_id=document.id,
                chunks_used=len(relevant_docs)
            )
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            raise
    
    async def summarize_document(
        self, 
        document: Document, 
        vector_store: FAISS,
        summary_type: str = "comprehensive"
    ) -> str:
        """
        Generate a summary of the entire document.
        
        Args:
            document: Document model instance
            vector_store: FAISS vector store
            summary_type: Type of summary (brief, comprehensive, key_points)
            
        Returns:
            Document summary
        """
        try:
            # Get all document chunks
            all_docs = vector_store.similarity_search("", k=1000)  # Get all chunks
            
            # Sort by chunk index to maintain order
            sorted_docs = sorted(
                all_docs, 
                key=lambda x: x.metadata.get('chunk_index', 0)
            )
            
            # Combine content
            full_content = "\n\n".join([doc.page_content for doc in sorted_docs])
            
            # Create summary prompt based on type
            if summary_type == "brief":
                prompt = f"""
Provide a brief 2-3 sentence summary of this document:

{full_content[:4000]}  # Limit content for brief summary

Summary:"""
            elif summary_type == "key_points":
                prompt = f"""
Extract the key points from this document as a bulleted list:

{full_content[:6000]}

Key Points:"""
            else:  # comprehensive
                prompt = f"""
Provide a comprehensive summary of this document including:
1. Main topic and purpose
2. Key findings or arguments
3. Important details and data
4. Conclusions

Document content:
{full_content[:8000]}

Comprehensive Summary:"""
            
            summary = await self.ai_service.generate_completion(prompt)
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            raise
    
    async def extract_key_concepts(
        self, 
        document: Document, 
        vector_store: FAISS
    ) -> List[Dict[str, Any]]:
        """
        Extract key concepts and entities from the document.
        
        Args:
            document: Document model instance
            vector_store: FAISS vector store
            
        Returns:
            List of key concepts with relevance scores
        """
        try:
            # Sample representative chunks
            sample_docs = vector_store.similarity_search("key concepts main topics", k=10)
            
            combined_content = "\n\n".join([doc.page_content for doc in sample_docs])
            
            prompt = f"""
Extract the key concepts, topics, and entities from this document content.
Return them as a structured list with importance ratings.

Content:
{combined_content[:4000]}

Key Concepts (format: Concept - Brief description - Importance (1-10)):"""
            
            concepts_text = await self.ai_service.generate_completion(prompt)
            
            # Parse the response (simplified - could use NER models)
            concepts = []
            for line in concepts_text.split('\n'):
                if ' - ' in line:
                    parts = line.split(' - ')
                    if len(parts) >= 3:
                        concepts.append({
                            "concept": parts[0].strip(),
                            "description": parts[1].strip(),
                            "importance": float(parts[2].strip().split('(')[-1].split(')')[0]) if '(' in parts[2] else 5.0
                        })
            
            return concepts
            
        except Exception as e:
            logger.error(f"Error extracting key concepts: {e}")
            return []
    
    async def find_related_passages(
        self,
        document: Document,
        vector_store: FAISS,
        query: str,
        max_passages: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find passages related to a specific query or topic.
        
        Args:
            document: Document model instance
            vector_store: FAISS vector store
            query: Search query
            max_passages: Maximum number of passages to return
            
        Returns:
            List of related passages with metadata
        """
        try:
            related_docs = vector_store.similarity_search_with_score(
                query, k=max_passages
            )
            
            passages = []
            for doc, score in related_docs:
                passages.append({
                    "content": doc.page_content,
                    "page_number": doc.metadata.get('page_number'),
                    "chunk_index": doc.metadata.get('chunk_index'),
                    "relevance_score": float(score),
                    "preview": doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                })
            
            return passages
            
        except Exception as e:
            logger.error(f"Error finding related passages: {e}")
            return []