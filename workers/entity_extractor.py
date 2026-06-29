"""
Entity extraction handler for the worker.

Phase 4: Implements the extract_entities job type.

This extracts named entities from document content and stores them in the database.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Extracts named entities from document content.
    
    This is a job handler that can be registered with the Worker.
    It handles the 'extract_entities' job type.
    """
    
    def __init__(self, backend):
        """
        Initialize the entity extractor.
        
        Args:
            backend: Storage backend
        """
        self.backend = backend
    
    def extract_entities(self, job: dict) -> dict:
        """
        Extract entities from a document.
        
        This is the job handler for 'extract_entities' jobs.
        
        Args:
            job: Job dict with document_id and job_type
            
        Returns:
            Dict with extraction results
        """
        document_id = job['document_id']
        job_id = job['id']
        
        logger.info(f"Starting entity extraction for document {document_id}")
        
        try:
            # Get document content
            content_data = self.backend.get_content(document_id)
            
            if not content_data or not content_data.get('content'):
                # No content yet - might need extract_text to run first
                raise ValueError(f"No content found for document {document_id}")
            
            content = content_data['content']
            logger.info(f"Extracting entities from {len(content)} chars of content")
            
            # Extract entities using the extractor
            entities = self._extract_entities_from_text(content)
            
            # Save entities to database
            saved_count = self._save_entities(document_id, entities)
            
            # Transition document to ENTITY_EXTRACTED
            try:
                self.backend.transition_document_status(
                    document_id,
                    'ENTITY_EXTRACTED'
                )
            except ValueError as e:
                logger.debug(f"State transition skipped: {e}")
            
            logger.info(f"Successfully extracted {saved_count} entities from document {document_id}")
            
            return {
                'document_id': document_id,
                'entities_extracted': saved_count,
                'entity_types': list(set(e.get('type') for e in entities if e.get('type')))
            }
            
        except Exception as e:
            logger.error(f"Entity extraction failed for document {document_id}: {e}")
            raise
    
    def _extract_entities_from_text(self, text: str) -> list:
        """
        Extract named entities from text.
        
        Uses simple pattern-based extraction for common entity types.
        
        Args:
            text: Input text
            
        Returns:
            List of entity dicts
        """
        entities = []
        
        # Try to use the real entity extractor if available
        try:
            from extractors.entity_extractor import EntityExtractor as RealExtractor
            extractor = RealExtractor()
            extracted = extractor.extract(text)
            
            if extracted:
                for entity in extracted:
                    entities.append({
                        'type': entity.get('type', 'UNKNOWN'),
                        'value': entity.get('value', entity.get('name', '')),
                        'normalized_value': entity.get('normalized_value', ''),
                        'confidence': entity.get('confidence', 0.8)
                    })
                return entities
        except ImportError:
            pass
        
        # Fallback: simple pattern-based extraction
        import re
        
        # Person names (capitalized words)
        person_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        for match in re.finditer(person_pattern, text):
            entities.append({
                'type': 'PERSON',
                'value': match.group(),
                'normalized_value': match.group().lower(),
                'confidence': 0.6
            })
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            entities.append({
                'type': 'EMAIL',
                'value': match.group(),
                'normalized_value': match.group().lower(),
                'confidence': 0.9
            })
        
        # URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        for match in re.finditer(url_pattern, text):
            entities.append({
                'type': 'URL',
                'value': match.group(),
                'normalized_value': match.group().lower(),
                'confidence': 0.9
            })
        
        # Organization names (common patterns)
        org_pattern = r'\b(?:The\s+)?(?:[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*\s+(?:Inc|LLC|Corp|Ltd|Company|Co)\.?)\b'
        for match in re.finditer(org_pattern, text):
            entities.append({
                'type': 'ORGANIZATION',
                'value': match.group(),
                'normalized_value': match.group().lower(),
                'confidence': 0.5
            })
        
        return entities
    
    def _save_entities(self, document_id: int, entities: list) -> int:
        """
        Save entities to the database.
        
        Args:
            document_id: Document ID
            entities: List of entity dicts
            
        Returns:
            Number of entities saved
        """
        if not entities:
            return 0
        
        saved_count = 0
        
        for entity in entities:
            entity_type = entity.get('type', 'UNKNOWN')
            value = entity.get('value', '')
            normalized = entity.get('normalized_value', value.lower())
            confidence = entity.get('confidence', 0.8)
            
            # Save entity
            entity_id = self.backend.save_entity(entity_type, value, normalized)
            
            if entity_id:
                # Link entity to document
                self.backend.add_entity_to_document(document_id, entity_id, 1)
                
                # Record evidence lineage
                if hasattr(self.backend, 'record_evidence'):
                    self.backend.record_evidence(
                        entity_id=entity_id,
                        document_id=document_id,
                        artifact_path=None,
                        plugin_name='entity_extractor',
                        confidence=confidence,
                        processing_time_ms=None,
                        version='1.0'
                    )
                
                saved_count += 1
        
        return saved_count
