"""
Event extraction handler for the worker.

Phase 4: Implements the extract_events job type.

This extracts date/time references and events from document content.
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class EventExtractor:
    """
    Extracts events and date/time references from document content.
    
    This is a job handler that can be registered with the Worker.
    It handles the 'extract_events' job type.
    """
    
    def __init__(self, backend):
        """
        Initialize the event extractor.
        
        Args:
            backend: Storage backend
        """
        self.backend = backend
    
    def extract_events(self, job: dict) -> dict:
        """
        Extract events from a document.
        
        This is the job handler for 'extract_events' jobs.
        
        Args:
            job: Job dict with document_id and job_type
            
        Returns:
            Dict with extraction results
        """
        document_id = job['document_id']
        job_id = job['id']
        
        logger.info(f"Starting event extraction for document {document_id}")
        
        try:
            # Get document content
            content_data = self.backend.get_content(document_id)
            
            if not content_data or not content_data.get('content'):
                raise ValueError(f"No content found for document {document_id}")
            
            content = content_data['content']
            logger.info(f"Extracting events from {len(content)} chars of content")
            
            # Extract events
            events = self._extract_events_from_text(content)
            
            # Save events to database
            saved_count = self._save_events(document_id, events)
            
            logger.info(f"Successfully extracted {saved_count} events from document {document_id}")
            
            return {
                'document_id': document_id,
                'events_extracted': saved_count,
                'event_types': list(set(e.get('event_type') for e in events if e.get('event_type')))
            }
            
        except Exception as e:
            logger.error(f"Event extraction failed for document {document_id}: {e}")
            raise
    
    def _extract_events_from_text(self, text: str) -> list:
        """
        Extract events and dates from text.
        
        Uses pattern-based extraction for common date formats and events.
        
        Args:
            text: Input text
            
        Returns:
            List of event dicts
        """
        events = []
        import re
        
        # Try to use the real event extractor if available
        try:
            from extractors.event_extractor import EventExtractor as RealExtractor
            extractor = RealExtractor()
            extracted = extractor.extract(text)
            
            if extracted:
                for event in extracted:
                    events.append({
                        'timestamp': event.get('timestamp', ''),
                        'event_type': event.get('type', 'GENERAL'),
                        'description': event.get('description', '')
                    })
                return events
        except ImportError:
            pass
        
        # Date patterns
        date_patterns = [
            # ISO format: 2024-01-15
            (r'\b(\d{4}-\d{2}-\d{2})\b', 'DATE'),
            # US format: 01/15/2024
            (r'\b(\d{1,2}/\d{1,2}/\d{4})\b', 'DATE'),
            # Written: January 15, 2024
            (r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b', 'DATE'),
            # Abbreviated: Jan 15, 2024
            (r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})\b', 'DATE'),
        ]
        
        seen_dates = set()
        for pattern, event_type in date_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                date_str = match.group(1)
                if date_str not in seen_dates:
                    seen_dates.add(date_str)
                    events.append({
                        'timestamp': date_str,
                        'event_type': event_type,
                        'description': f"Date reference: {date_str}"
                    })
        
        # Time patterns
        time_pattern = r'\b(\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM))?)\b'
        seen_times = set()
        for match in re.finditer(time_pattern, text, re.IGNORECASE):
            time_str = match.group(1)
            if time_str not in seen_times:
                seen_times.add(time_str)
                events.append({
                    'timestamp': time_str,
                    'event_type': 'TIME',
                    'description': f"Time reference: {time_str}"
                })
        
        # Relative date references
        relative_patterns = [
            (r'\btoday\b', 'RELATIVE', 'Today'),
            (r'\byesterday\b', 'RELATIVE', 'Yesterday'),
            (r'\btomorrow\b', 'RELATIVE', 'Tomorrow'),
            (r'\blast\s+week\b', 'RELATIVE', 'Last week'),
            (r'\bnext\s+week\b', 'RELATIVE', 'Next week'),
            (r'\blast\s+month\b', 'RELATIVE', 'Last month'),
            (r'\bnext\s+month\b', 'RELATIVE', 'Next month'),
        ]
        
        for pattern, event_type, description in relative_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                events.append({
                    'timestamp': datetime.now().isoformat(),
                    'event_type': event_type,
                    'description': description
                })
        
        return events
    
    def _save_events(self, document_id: int, events: list) -> int:
        """
        Save events to the database.
        
        Args:
            document_id: Document ID
            events: List of event dicts
            
        Returns:
            Number of events saved
        """
        if not events:
            return 0
        
        saved_count = 0
        
        for event in events:
            timestamp = event.get('timestamp', '')
            event_type = event.get('event_type', 'GENERAL')
            description = event.get('description', '')
            
            # Save event
            event_id = self.backend.save_event(timestamp, event_type, description)
            
            if event_id:
                # Link event to document
                self.backend.add_event_to_document(document_id, event_id)
                saved_count += 1
        
        return saved_count
