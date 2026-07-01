"""
Content extraction handler for the worker.

Phase 3A: Implements the extract_text job type.

This extracts text content from documents and stores it in the database.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from environment import get_library_root

logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    Extracts text content from documents.
    
    This is a job handler that can be registered with the Worker.
    It handles the 'extract_text' job type.
    
    The actual text extraction is delegated to the appropriate parser
    based on file extension.
    """
    
    def __init__(self, backend, library_root: str = None):
        """
        Initialize the content extractor.
        
        Args:
            backend: Storage backend
            library_root: Root path of the document library
        """
        self.backend = backend
        self.library_root = library_root or get_library_root()
    
    def extract_text(self, job: dict) -> dict:
        """
        Extract text content from a document.
        
        This is the job handler for 'extract_text' jobs.
        
        Args:
            job: Job dict with document_id and job_type
            
        Returns:
            Dict with extraction results
        """
        document_id = job['document_id']
        job_id = job['id']
        
        logger.info(f"Starting content extraction for document {document_id}")
        
        try:
            # Get document info
            conn = self.backend._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, path, parser FROM documents WHERE id = %s", (document_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            
            if not row:
                raise ValueError(f"Document {document_id} not found")
            
            doc_id, doc_path, parser = row
            
            # Resolve full path
            if os.path.isabs(doc_path):
                full_path = Path(doc_path)
            else:
                full_path = Path(self.library_root) / doc_path
            
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {full_path}")
            
            # Extract content using parser
            content = self._extract_content(full_path, parser)
            
            if content is None:
                raise ValueError(f"No content extracted from {full_path}")
            
            # Save content to database
            success = self.backend.save_content(document_id, content, 'textract')
            
            if not success:
                raise RuntimeError(f"Failed to save content for document {document_id}")
            
            # Update document status to CONTENT_EXTRACTED
            try:
                self.backend.transition_document_status(
                    document_id,
                    'CONTENT_EXTRACTED'
                )
            except ValueError as e:
                # State transition might fail if already in that state
                logger.debug(f"State transition skipped: {e}")
            
            logger.info(f"Successfully extracted {len(content)} chars from document {document_id}")
            
            return {
                'document_id': document_id,
                'content_length': len(content),
                'content_hash': self._hash_content(content)
            }
            
        except Exception as e:
            logger.error(f"Content extraction failed for document {document_id}: {e}")
            raise
    
    def _extract_content(self, filepath: Path, parser: str = None) -> Optional[str]:
        """
        Extract text content from a file.
        
        Args:
            filepath: Path to the file
            parser: Parser name (optional, inferred from extension if not provided)
            
        Returns:
            Extracted text content, or None if extraction failed
        """
        # Try to use parser registry if available
        try:
            from parsers.parser_registry import ParserRegistry
            
            registry = ParserRegistry()
            parser_obj = parser and registry.get_parser(filepath) or registry.get_parser(filepath)
            
            if parser_obj:
                parsed = parser_obj.parse(filepath)
                if parsed:
                    return parsed.get('text', '')
        except ImportError:
            pass
        
        # Fallback: read as plain text
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Failed to read {filepath} as text: {e}")
        
        return None
    
    def _hash_content(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        import hashlib
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
