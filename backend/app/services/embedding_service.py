# backend/app/services/embedding_service.py
"""
Embedding service for generating and managing document embeddings
using sentence-transformers with FAISS vector store.
"""

import asyncio
import logging
import os
import pickle
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

import numpy as np

# Disable sentence-transformers for now due to compatibility issues
SENTENCE_TRANSFORMERS_AVAILABLE = False
SentenceTransformer = None

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False

from app.config.settings import settings
from app.core.exceptions import EmbeddingError
from app.models.document import DocumentChunk

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing document embeddings."""
    
    def __init__(self):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.info("sentence-transformers is not available. Using improved hash-based embeddings for testing.")
            self.model = None
            self.embedding_dim = 384  # Default dimension for all-MiniLM-L6-v2
        else:
            try:
                self.model = SentenceTransformer(settings.embedding_model_name)
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
                logger.info(f"Initialized embedding service with model: {settings.embedding_model_name}")
                logger.info(f"Embedding dimension: {self.embedding_dim}")
            except Exception as e:
                logger.error(f"Failed to initialize embedding model: {e}")
                self.model = None
                self.embedding_dim = 384
        
        # Ensure vector store directory exists
        os.makedirs(settings.vector_store_path, exist_ok=True)
    
    async def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            numpy array of embeddings
        """
        try:
            if not texts:
                raise EmbeddingError("No texts provided for embedding")
            
            if self.model is None:
                # Use improved word-frequency-based embeddings for testing
                logger.info("Using word-frequency-based embeddings for testing. This provides basic semantic similarity.")
                import hashlib
                import re
                from collections import Counter
                
                embeddings = []
                for text in texts:
                    # Clean and tokenize text
                    words = re.findall(r'\b\w+\b', text.lower())
                    word_counts = Counter(words)
                    
                    # Create embedding based on word frequencies and characteristics
                    embedding = np.zeros(self.embedding_dim, dtype=np.float32)
                    
                    # Use text characteristics for embedding
                    text_features = [
                        len(text) / 1000.0,  # Text length
                        len(words) / 100.0,  # Word count
                        len(set(words)) / len(words) if words else 0,  # Vocabulary diversity
                        sum(1 for w in words if len(w) > 6) / len(words) if words else 0,  # Complex words ratio
                        text.count('.') / len(text) if text else 0,  # Sentence density
                        text.count('?') / len(text) if text else 0,  # Question density
                        text.count('!') / len(text) if text else 0,  # Exclamation density
                    ]
                    
                    # Hash most common words for semantic features
                    common_words = [word for word, _ in word_counts.most_common(50)]
                    for i, word in enumerate(common_words[:50]):
                        word_hash = int(hashlib.md5(word.encode()).hexdigest()[:8], 16)
                        idx = (word_hash % (self.embedding_dim - 20)) + 10
                        embedding[idx] += word_counts[word] / len(words) if words else 0
                    
                    # Add text features to the end
                    for i, feature in enumerate(text_features[:7]):
                        embedding[-(i+1)] = min(feature, 1.0)
                    
                    # Normalize the embedding
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = embedding / norm
                    
                    embeddings.append(embedding)
                
                return np.array(embeddings, dtype=np.float32)
            
            # Run embedding generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, 
                self.model.encode, 
                texts
            )
            
            # Ensure embeddings are float32 for FAISS
            embeddings = embeddings.astype(np.float32)
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise EmbeddingError(f"Failed to generate embeddings: {str(e)}")
    
    async def generate_single_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text string to embed
            
        Returns:
            numpy array embedding
        """
        try:
            embeddings = await self.generate_embeddings([text])
            return embeddings[0]
            
        except Exception as e:
            logger.error(f"Error generating single embedding: {e}")
            raise EmbeddingError(f"Failed to generate single embedding: {str(e)}")
    
    async def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score
        """
        try:
            # Normalize embeddings
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Compute cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            raise EmbeddingError(f"Failed to compute similarity: {str(e)}")
    
    async def batch_compute_similarities(
        self, 
        query_embedding: np.ndarray, 
        document_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute similarities between query and multiple document embeddings.
        
        Args:
            query_embedding: Query embedding vector
            document_embeddings: Array of document embeddings
            
        Returns:
            Array of similarity scores
        """
        try:
            # Normalize embeddings
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            doc_norms = document_embeddings / np.linalg.norm(document_embeddings, axis=1, keepdims=True)
            
            # Compute cosine similarities
            similarities = np.dot(doc_norms, query_norm)
            return similarities
            
        except Exception as e:
            logger.error(f"Error computing batch similarities: {e}")
            raise EmbeddingError(f"Failed to compute batch similarities: {str(e)}")
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings generated by this service."""
        return self.embedding_dim
    
    async def validate_embedding(self, embedding: np.ndarray) -> bool:
        """
        Validate that an embedding has the correct dimensions and format.
        
        Args:
            embedding: Embedding to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not isinstance(embedding, np.ndarray):
                return False
            
            if embedding.dtype != np.float32:
                return False
            
            if len(embedding.shape) != 1:
                return False
            
            if embedding.shape[0] != self.embedding_dim:
                return False
            
            # Check for NaN or infinite values
            if np.any(np.isnan(embedding)) or np.any(np.isinf(embedding)):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating embedding: {e}")
            return False
    
    async def save_embeddings_batch(
        self, 
        embeddings: np.ndarray, 
        metadata: List[Dict[str, Any]], 
        file_path: str
    ) -> None:
        """
        Save embeddings and metadata to file.
        
        Args:
            embeddings: Array of embeddings
            metadata: List of metadata dictionaries
            file_path: Path to save file
        """
        try:
            data = {
                'embeddings': embeddings,
                'metadata': metadata,
                'dimension': self.embedding_dim,
                'model_name': settings.embedding_model_name
            }
            
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"Saved {len(embeddings)} embeddings to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving embeddings: {e}")
            raise EmbeddingError(f"Failed to save embeddings: {str(e)}")
    
    async def load_embeddings_batch(self, file_path: str) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Load embeddings and metadata from file.
        
        Args:
            file_path: Path to load file
            
        Returns:
            Tuple of (embeddings, metadata)
        """
        try:
            if not os.path.exists(file_path):
                raise EmbeddingError(f"Embedding file not found: {file_path}")
            
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            embeddings = data['embeddings']
            metadata = data['metadata']
            
            # Validate loaded data
            if embeddings.shape[1] != self.embedding_dim:
                raise EmbeddingError(f"Embedding dimension mismatch: expected {self.embedding_dim}, got {embeddings.shape[1]}")
            
            logger.info(f"Loaded {len(embeddings)} embeddings from {file_path}")
            return embeddings, metadata
            
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            raise EmbeddingError(f"Failed to load embeddings: {str(e)}")
    
    async def cleanup_embedding_files(self, document_id: UUID) -> None:
        """
        Clean up embedding files for a document.
        
        Args:
            document_id: Document ID to clean up
        """
        try:
            embedding_file = os.path.join(
                settings.vector_store_path, 
                f"embeddings_{document_id}.pkl"
            )
            
            if os.path.exists(embedding_file):
                os.remove(embedding_file)
                logger.info(f"Cleaned up embedding file for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up embedding files: {e}")
            raise EmbeddingError(f"Failed to cleanup embedding files: {str(e)}")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the embedding model.
        
        Returns:
            Dictionary with model information
        """
        try:
            if self.model is None:
                return {
                    'model_name': settings.embedding_model_name,
                    'embedding_dimension': self.embedding_dim,
                    'status': 'not_available',
                    'error': 'Model not loaded'
                }
            
            return {
                'model_name': settings.embedding_model_name,
                'embedding_dimension': self.embedding_dim,
                'max_sequence_length': self.model.max_seq_length,
                'model_type': type(self.model).__name__,
                'device': str(self.model.device),
                'status': 'available'
            }
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {'error': str(e)}