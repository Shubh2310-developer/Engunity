# backend/app/services/vector_store.py
"""
FAISS vector store service for semantic search and retrieval.
"""

import asyncio
import logging
import os
import pickle
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

import numpy as np
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False

from app.config.settings import settings
from app.core.exceptions import VectorStoreError
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """FAISS-based vector store for document chunks."""
    
    def __init__(self, embedding_service: EmbeddingService):
        if not FAISS_AVAILABLE:
            raise VectorStoreError("faiss is not installed. Please install faiss-cpu or faiss-gpu to use vector search.")
        
        self.embedding_service = embedding_service
        self.embedding_dim = embedding_service.get_embedding_dimension()
        
        # Ensure vector store directory exists
        os.makedirs(settings.vector_store_path, exist_ok=True)
        
        logger.info(f"Initialized FAISS vector store with dimension: {self.embedding_dim}")
    
    async def create_index(self, document_id: UUID, embeddings: np.ndarray, metadata: List[Dict[str, Any]]) -> None:
        """
        Create a new FAISS index for a document.
        
        Args:
            document_id: Document ID
            embeddings: Array of embeddings
            metadata: List of metadata for each embedding
        """
        try:
            if len(embeddings) == 0:
                raise VectorStoreError("No embeddings provided for index creation")
            
            if embeddings.shape[1] != self.embedding_dim:
                raise VectorStoreError(f"Embedding dimension mismatch: expected {self.embedding_dim}, got {embeddings.shape[1]}")
            
            # Create FAISS index
            index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
            
            # Validate embeddings before processing
            logger.info(f"Input embeddings shape: {embeddings.shape}, dtype: {embeddings.dtype}")
            
            # Normalize embeddings for cosine similarity
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            # Avoid division by zero
            norms = np.where(norms == 0, 1, norms)
            normalized_embeddings = embeddings / norms
            
            logger.info(f"Normalized embeddings shape: {normalized_embeddings.shape}, dtype: {normalized_embeddings.dtype}")
            
            # Ensure float32 and contiguous
            normalized_embeddings = np.ascontiguousarray(normalized_embeddings.astype(np.float32))
            
            # Add embeddings to index
            index.add(normalized_embeddings)
            # Save index and metadata
            index_path = self._get_index_path(document_id)
            metadata_path = self._get_metadata_path(document_id)
            
            # Save FAISS index
            faiss.write_index(index, index_path)
            
            # Save metadata
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info(f"Created FAISS index for document {document_id} with {len(embeddings)} vectors")
            
        except Exception as e:
            logger.error(f"Error creating FAISS index: {e}")
            raise VectorStoreError(f"Failed to create FAISS index: {str(e)}")
    
    async def search(
        self, 
        document_id: UUID, 
        query_embedding: np.ndarray, 
        k: int = 5,
        threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in the document index.
        
        Args:
            document_id: Document ID to search in
            query_embedding: Query embedding vector
            k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of search results with metadata and scores
        """
        try:
            # Load index and metadata
            index, metadata = await self._load_index(document_id)
            
            if index is None:
                logger.warning(f"No index found for document {document_id}")
                return []
            
            # Normalize query embedding
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            query_norm = query_norm.astype(np.float32).reshape(1, -1)
            
            # Search
            scores, indices = index.search(query_norm, min(k, index.ntotal))
            
            # Process results
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx == -1:  # FAISS returns -1 for invalid indices
                    break
                
                if score >= threshold:
                    result = {
                        'chunk_id': metadata[idx]['chunk_id'],
                        'content': metadata[idx]['content'],
                        'page_number': metadata[idx].get('page_number'),
                        'chunk_index': metadata[idx].get('chunk_index'),
                        'relevance_score': float(score),
                        'metadata': metadata[idx]
                    }
                    results.append(result)
            
            logger.info(f"Found {len(results)} similar chunks for document {document_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching FAISS index: {e}")
            raise VectorStoreError(f"Failed to search FAISS index: {str(e)}")
    
    async def update_index(self, document_id: UUID, embeddings: np.ndarray, metadata: List[Dict[str, Any]]) -> None:
        """
        Update an existing FAISS index with new embeddings.
        
        Args:
            document_id: Document ID
            embeddings: New embeddings to add
            metadata: Metadata for new embeddings
        """
        try:
            # Load existing index and metadata
            index, existing_metadata = await self._load_index(document_id)
            
            if index is None:
                # Create new index if it doesn't exist
                await self.create_index(document_id, embeddings, metadata)
                return
            
            # Normalize new embeddings
            normalized_embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Add new embeddings to index
            index.add(normalized_embeddings.astype(np.float32))
            
            # Update metadata
            updated_metadata = existing_metadata + metadata
            
            # Save updated index and metadata
            index_path = self._get_index_path(document_id)
            metadata_path = self._get_metadata_path(document_id)
            
            faiss.write_index(index, index_path)
            
            with open(metadata_path, 'wb') as f:
                pickle.dump(updated_metadata, f)
            
            logger.info(f"Updated FAISS index for document {document_id} with {len(embeddings)} new vectors")
            
        except Exception as e:
            logger.error(f"Error updating FAISS index: {e}")
            raise VectorStoreError(f"Failed to update FAISS index: {str(e)}")
    
    async def delete_index(self, document_id: UUID) -> None:
        """
        Delete FAISS index for a document.
        
        Args:
            document_id: Document ID to delete index for
        """
        try:
            index_path = self._get_index_path(document_id)
            metadata_path = self._get_metadata_path(document_id)
            
            # Delete index file
            if os.path.exists(index_path):
                os.remove(index_path)
                logger.info(f"Deleted FAISS index file for document {document_id}")
            
            # Delete metadata file
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
                logger.info(f"Deleted metadata file for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error deleting FAISS index: {e}")
            raise VectorStoreError(f"Failed to delete FAISS index: {str(e)}")
    
    async def index_exists(self, document_id: UUID) -> bool:
        """
        Check if index exists for a document.
        
        Args:
            document_id: Document ID to check
            
        Returns:
            True if index exists, False otherwise
        """
        try:
            index_path = self._get_index_path(document_id)
            metadata_path = self._get_metadata_path(document_id)
            
            return os.path.exists(index_path) and os.path.exists(metadata_path)
            
        except Exception as e:
            logger.error(f"Error checking index existence: {e}")
            return False
    
    async def get_index_stats(self, document_id: UUID) -> Dict[str, Any]:
        """
        Get statistics about a document's index.
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary with index statistics
        """
        try:
            index, metadata = await self._load_index(document_id)
            
            if index is None:
                return {'error': 'Index not found'}
            
            stats = {
                'document_id': str(document_id),
                'total_vectors': index.ntotal,
                'embedding_dimension': index.d,
                'index_type': type(index).__name__,
                'metadata_count': len(metadata),
                'index_size_bytes': os.path.getsize(self._get_index_path(document_id)) if os.path.exists(self._get_index_path(document_id)) else 0,
                'metadata_size_bytes': os.path.getsize(self._get_metadata_path(document_id)) if os.path.exists(self._get_metadata_path(document_id)) else 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {'error': str(e)}
    
    async def rebuild_index(self, document_id: UUID, embeddings: np.ndarray, metadata: List[Dict[str, Any]]) -> None:
        """
        Rebuild index from scratch.
        
        Args:
            document_id: Document ID
            embeddings: All embeddings for the document
            metadata: All metadata for the document
        """
        try:
            # Delete existing index
            await self.delete_index(document_id)
            
            # Create new index
            await self.create_index(document_id, embeddings, metadata)
            
            logger.info(f"Rebuilt FAISS index for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error rebuilding FAISS index: {e}")
            raise VectorStoreError(f"Failed to rebuild FAISS index: {str(e)}")
    
    async def batch_search(
        self, 
        document_ids: List[UUID], 
        query_embedding: np.ndarray, 
        k: int = 5,
        threshold: float = 0.0
    ) -> Dict[UUID, List[Dict[str, Any]]]:
        """
        Search across multiple document indices.
        
        Args:
            document_ids: List of document IDs to search
            query_embedding: Query embedding vector
            k: Number of results per document
            threshold: Minimum similarity threshold
            
        Returns:
            Dictionary mapping document IDs to search results
        """
        try:
            results = {}
            
            # Search each document concurrently
            tasks = []
            for doc_id in document_ids:
                task = self.search(doc_id, query_embedding, k, threshold)
                tasks.append((doc_id, task))
            
            # Wait for all searches to complete
            for doc_id, task in tasks:
                try:
                    search_results = await task
                    results[doc_id] = search_results
                except Exception as e:
                    logger.error(f"Error searching document {doc_id}: {e}")
                    results[doc_id] = []
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch search: {e}")
            raise VectorStoreError(f"Failed to perform batch search: {str(e)}")
    
    def _get_index_path(self, document_id: UUID) -> str:
        """Get file path for document index."""
        return os.path.join(settings.vector_store_path, f"faiss_index_{document_id}.index")
    
    def _get_metadata_path(self, document_id: UUID) -> str:
        """Get file path for document metadata."""
        return os.path.join(settings.vector_store_path, f"faiss_metadata_{document_id}.pkl")
    
    async def _load_index(self, document_id: UUID) -> Tuple[Optional[faiss.Index], List[Dict[str, Any]]]:
        """
        Load FAISS index and metadata for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Tuple of (index, metadata) or (None, []) if not found
        """
        try:
            index_path = self._get_index_path(document_id)
            metadata_path = self._get_metadata_path(document_id)
            
            if not os.path.exists(index_path) or not os.path.exists(metadata_path):
                return None, []
            
            # Load index
            index = faiss.read_index(index_path)
            
            # Load metadata
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            return index, metadata
            
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            return None, []
    
    async def cleanup_all_indices(self) -> None:
        """Clean up all FAISS indices in the vector store directory."""
        try:
            vector_store_path = settings.vector_store_path
            
            for filename in os.listdir(vector_store_path):
                if filename.startswith('faiss_index_') or filename.startswith('faiss_metadata_'):
                    file_path = os.path.join(vector_store_path, filename)
                    os.remove(file_path)
                    logger.info(f"Cleaned up file: {filename}")
            
        except Exception as e:
            logger.error(f"Error cleaning up indices: {e}")
            raise VectorStoreError(f"Failed to cleanup indices: {str(e)}")
    
    async def get_all_index_stats(self) -> Dict[str, Any]:
        """Get statistics for all indices."""
        try:
            vector_store_path = settings.vector_store_path
            
            total_indices = 0
            total_size = 0
            
            for filename in os.listdir(vector_store_path):
                if filename.startswith('faiss_index_') or filename.startswith('faiss_metadata_'):
                    file_path = os.path.join(vector_store_path, filename)
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    
                    if filename.startswith('faiss_index_'):
                        total_indices += 1
            
            return {
                'total_indices': total_indices,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'vector_store_path': vector_store_path
            }
            
        except Exception as e:
            logger.error(f"Error getting all index stats: {e}")
            return {'error': str(e)}