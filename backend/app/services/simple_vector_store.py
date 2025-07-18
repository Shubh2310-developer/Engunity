# backend/app/services/simple_vector_store.py
"""
Simple vector store service using basic similarity search without FAISS.
This is a fallback implementation when FAISS is not available or not working.
"""

import asyncio
import logging
import os
import pickle
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

import numpy as np

from app.config.settings import settings
from app.core.exceptions import VectorStoreError
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class SimpleVectorStore:
    """Simple vector store using basic similarity search."""
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.embedding_dim = embedding_service.get_embedding_dimension()
        
        # Ensure vector store directory exists
        os.makedirs(settings.vector_store_path, exist_ok=True)
        
        logger.info(f"Initialized Simple vector store with dimension: {self.embedding_dim}")
    
    async def create_index(self, document_id: UUID, embeddings: np.ndarray, metadata: List[Dict[str, Any]]) -> None:
        """
        Create a new vector store for a document.
        
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
            
            # Validate embeddings format
            logger.info(f"Input embeddings shape: {embeddings.shape}, dtype: {embeddings.dtype}")
            
            # Normalize embeddings for cosine similarity
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
            normalized_embeddings = embeddings / norms
            
            logger.info(f"Normalized embeddings shape: {normalized_embeddings.shape}, dtype: {normalized_embeddings.dtype}")
            
            # Save embeddings and metadata
            data = {
                'embeddings': normalized_embeddings.astype(np.float32),
                'metadata': metadata,
                'document_id': str(document_id),
                'embedding_dimension': self.embedding_dim
            }
            
            # Save to file
            index_path = self._get_index_path(document_id)
            with open(index_path, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"Created simple vector store for document {document_id} with {len(embeddings)} vectors")
            
        except Exception as e:
            logger.error(f"Error creating simple vector store: {e}")
            raise VectorStoreError(f"Failed to create simple vector store: {str(e)}")
    
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
            # Load index data
            data = await self._load_index(document_id)
            
            if data is None:
                logger.warning(f"No index found for document {document_id}")
                return []
            
            embeddings = data['embeddings']
            metadata = data['metadata']
            
            # Normalize query embedding
            query_norm = np.linalg.norm(query_embedding)
            if query_norm == 0:
                logger.warning("Query embedding has zero norm")
                return []
            
            query_embedding = query_embedding / query_norm
            
            # Compute cosine similarities
            similarities = np.dot(embeddings, query_embedding.flatten())
            
            # Get top k results
            top_k_indices = np.argsort(similarities)[::-1][:k]
            
            # Process results
            results = []
            for idx in top_k_indices:
                score = similarities[idx]
                
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
            logger.error(f"Error searching simple vector store: {e}")
            raise VectorStoreError(f"Failed to search simple vector store: {str(e)}")
    
    async def update_index(self, document_id: UUID, embeddings: np.ndarray, metadata: List[Dict[str, Any]]) -> None:
        """
        Update an existing vector store with new embeddings.
        
        Args:
            document_id: Document ID
            embeddings: New embeddings to add
            metadata: Metadata for new embeddings
        """
        try:
            # Load existing data
            existing_data = await self._load_index(document_id)
            
            if existing_data is None:
                # Create new index if it doesn't exist
                await self.create_index(document_id, embeddings, metadata)
                return
            
            # Combine existing and new embeddings
            existing_embeddings = existing_data['embeddings']
            existing_metadata = existing_data['metadata']
            
            # Normalize new embeddings
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            normalized_embeddings = embeddings / norms
            
            # Combine data
            combined_embeddings = np.vstack([existing_embeddings, normalized_embeddings])
            combined_metadata = existing_metadata + metadata
            
            # Save updated data
            await self.create_index(document_id, combined_embeddings, combined_metadata)
            
            logger.info(f"Updated simple vector store for document {document_id} with {len(embeddings)} new vectors")
            
        except Exception as e:
            logger.error(f"Error updating simple vector store: {e}")
            raise VectorStoreError(f"Failed to update simple vector store: {str(e)}")
    
    async def delete_index(self, document_id: UUID) -> None:
        """
        Delete vector store for a document.
        
        Args:
            document_id: Document ID to delete index for
        """
        try:
            index_path = self._get_index_path(document_id)
            
            if os.path.exists(index_path):
                os.remove(index_path)
                logger.info(f"Deleted simple vector store for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error deleting simple vector store: {e}")
            raise VectorStoreError(f"Failed to delete simple vector store: {str(e)}")
    
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
            return os.path.exists(index_path)
            
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
            data = await self._load_index(document_id)
            
            if data is None:
                return {'error': 'Index not found'}
            
            embeddings = data['embeddings']
            metadata = data['metadata']
            
            stats = {
                'document_id': str(document_id),
                'total_vectors': len(embeddings),
                'embedding_dimension': embeddings.shape[1],
                'index_type': 'SimpleVectorStore',
                'metadata_count': len(metadata),
                'index_size_bytes': os.path.getsize(self._get_index_path(document_id)) if os.path.exists(self._get_index_path(document_id)) else 0
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
            
            logger.info(f"Rebuilt simple vector store for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error rebuilding simple vector store: {e}")
            raise VectorStoreError(f"Failed to rebuild simple vector store: {str(e)}")
    
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
            
            # Search each document
            for doc_id in document_ids:
                try:
                    search_results = await self.search(doc_id, query_embedding, k, threshold)
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
        return os.path.join(settings.vector_store_path, f"simple_index_{document_id}.pkl")
    
    async def _load_index(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Load vector store data for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary with embeddings and metadata or None if not found
        """
        try:
            index_path = self._get_index_path(document_id)
            
            if not os.path.exists(index_path):
                return None
            
            with open(index_path, 'rb') as f:
                data = pickle.load(f)
            
            return data
            
        except Exception as e:
            logger.error(f"Error loading simple vector store: {e}")
            return None
    
    async def cleanup_all_indices(self) -> None:
        """Clean up all vector stores in the directory."""
        try:
            vector_store_path = settings.vector_store_path
            
            for filename in os.listdir(vector_store_path):
                if filename.startswith('simple_index_'):
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
                if filename.startswith('simple_index_'):
                    file_path = os.path.join(vector_store_path, filename)
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
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