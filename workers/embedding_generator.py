"""
Embedding generation handler for the worker.

Phase 4: Implements the generate_embeddings job type.

This generates vector embeddings for document content.

Operation Plugin Foundation: Added plugin identity fields for provenance tracking.
"""

import logging
from typing import Optional
from environment import get_embedding_model
from .base import BaseWorker

logger = logging.getLogger(__name__)


class EmbeddingGenerator(BaseWorker):
    """
    Generates vector embeddings for document content.

    This is a job handler that can be registered with the Worker.
    It handles the 'generate_embeddings' job type.

    Supports:
    - OpenAI embeddings (text-embedding-ada-002)
    - Sentence transformers (local, open-source)
    - TF-IDF fallback (no API required)

    Operation Plugin Foundation: Added plugin identity fields for provenance.
    Note: ENGINE_NAME is set dynamically based on the detected/selected model.
    """

    # Operation Plugin Foundation: Plugin identity
    # Base values - ENGINE_NAME is set dynamically based on model
    PLUGIN_NAME = 'embeddings.vector.default'
    ENGINE_NAME = 'unknown'
    PLUGIN_VERSION = '1.0.0'
    
    def __init__(self, backend, model_name: str = None):
        """
        Initialize the embedding generator.
        
        Args:
            backend: Storage backend
            model_name: Embedding model to use
        """
        self.backend = backend
        self.model_name = model_name or self._detect_model()
        self._embedding_model = None
    
    def _detect_model(self) -> str:
        """Detect the best available embedding model and set ENGINE_NAME."""
        import os

        # Check environment variable
        env_model = get_embedding_model()
        if env_model:
            self.ENGINE_NAME = env_model
            return env_model

        # Check for OpenAI
        if os.environ.get('OPENAI_API_KEY'):
            self.ENGINE_NAME = 'openai-ada002'
            return 'openai'

        # Check for sentence-transformers
        try:
            import sentence_transformers
            self.ENGINE_NAME = 'sentence-transformers'
            return 'sentence-transformers'
        except ImportError:
            pass

        # Default to TF-IDF
        self.ENGINE_NAME = 'tfidf'
        return 'tfidf'
    
    def process(self, job: dict) -> dict:
        """
        Generate embeddings for a document.
        
        This is the job handler for 'generate_embeddings' jobs.
        
        Args:
            job: Job dict with document_id and job_type
            
        Returns:
            Dict with generation results
        """
        document_id = job['document_id']
        job_id = job['id']
        
        logger.info(f"Starting embedding generation for document {document_id}")
        
        try:
            # Get document content
            content_data = self.backend.get_content(document_id)
            
            if not content_data or not content_data.get('content'):
                raise ValueError(f"No content found for document {document_id}")
            
            content = content_data['content']
            logger.info(f"Generating embeddings for {len(content)} chars of content")
            
            # Generate embeddings
            embedding_result = self._generate_embedding(content)
            
            if embedding_result is None:
                raise ValueError("Embedding generation returned no result")
            
            # Save embedding to database
            success = self.backend.save_embedding(document_id, embedding_result['vector'])
            
            if not success:
                raise RuntimeError(f"Failed to save embedding for document {document_id}")
            
            # Transition document to EMBEDDED
            try:
                self.backend.transition_document_status(
                    document_id,
                    'EMBEDDED'
                )
            except ValueError as e:
                logger.debug(f"State transition skipped: {e}")
            
            logger.info(f"Successfully generated embedding for document {document_id} "
                       f"({len(embedding_result['vector'])} dimensions)")
            
            return {
                'document_id': document_id,
                'dimensions': len(embedding_result['vector']),
                'model': embedding_result.get('model', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Embedding generation failed for document {document_id}: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> Optional[dict]:
        """
        Generate embedding for text.
        
        Args:
            text: Input text
            
        Returns:
            Dict with 'vector' and 'model' keys
        """
        if self.model_name == 'openai':
            return self._generate_openai_embedding(text)
        elif self.model_name == 'sentence-transformers':
            return self._generate_sentence_transformer_embedding(text)
        else:
            return self._generate_tfidf_embedding(text)
    
    def _generate_openai_embedding(self, text: str) -> Optional[dict]:
        """Generate embedding using OpenAI API."""
        import os
        import hashlib
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OpenAI API key not set, falling back to TF-IDF")
            return self._generate_tfidf_embedding(text)
        
        try:
            import openai
            
            # Truncate text if too long (OpenAI has 8191 token limit)
            max_chars = 8000
            if len(text) > max_chars:
                text = text[:max_chars]
            
            response = openai.Embedding.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            return {
                'vector': response['data'][0]['embedding'],
                'model': 'text-embedding-ada-002'
            }
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            return None
    
    def _generate_sentence_transformer_embedding(self, text: str) -> Optional[dict]:
        """Generate embedding using sentence-transformers."""
        try:
            if self._embedding_model is None:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Truncate text if too long
            max_chars = 5000
            if len(text) > max_chars:
                text = text[:max_chars]
            
            embedding = self._embedding_model.encode(text)
            
            return {
                'vector': embedding.tolist(),
                'model': 'all-MiniLM-L6-v2'
            }
        except Exception as e:
            logger.error(f"Sentence transformer embedding failed: {e}")
            return None
    
    def _generate_tfidf_embedding(self, text: str) -> Optional[dict]:
        """
        Generate TF-IDF based embedding as fallback.
        
        This creates a sparse vector using TF-IDF weights.
        Less semantic than transformer-based embeddings but works offline.
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from scipy.sparse import csr_matrix
            
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=384,  # Match embedding dimension
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2
            )
            
            # Fit and transform
            tfidf_matrix = vectorizer.fit_transform([text])
            
            # Convert to dense list
            vector = tfidf_matrix.toarray()[0].tolist()
            
            # Normalize
            import math
            norm = math.sqrt(sum(x * x for x in vector))
            if norm > 0:
                vector = [x / norm for x in vector]
            
            return {
                'vector': vector,
                'model': 'tfidf'
            }
        except ImportError:
            # No sklearn available - create simple hash-based vector
            logger.warning("sklearn not available, using hash-based embedding")
            return self._generate_hash_embedding(text)
        except Exception as e:
            logger.error(f"TF-IDF embedding failed: {e}")
            return None
    
    def _generate_hash_embedding(self, text: str) -> Optional[dict]:
        """
        Generate a simple hash-based embedding as last resort.
        
        Creates a fixed-dimension vector from character n-gram hashes.
        """
        import hashlib
        import struct
        
        # Dimension of the embedding vector
        dimensions = 256
        
        # Simple n-gram hashing
        n = 3  # trigrams
        ngrams = [text[i:i+n] for i in range(len(text) - n + 1)]
        
        # Initialize vector
        vector = [0.0] * dimensions
        
        # Hash each n-gram and update vector
        for ngram in ngrams[:1000]:  # Limit to first 1000 n-grams
            hash_bytes = hashlib.sha256(ngram.encode()).digest()
            hash_int = struct.unpack('<Q', hash_bytes[:8])[0]
            
            for i in range(dimensions):
                # Use bit i of hash to update dimension i
                if hash_int & (1 << i):
                    vector[i] += 1.0
        
        # Normalize
        import math
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]
        
        return {
            'vector': vector,
            'model': 'hash-ngram'
        }