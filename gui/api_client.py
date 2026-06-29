"""
Librarian GUI API Client

Centralizes all API calls. The GUI must never import core/*, storage/*,
parsers/*, extractors/*, or postgres_backend.py. All communication happens
through this client only.
"""

import os
import requests
from typing import Optional


class LibrarianAPIClient:
    """Client for communicating with Librarian REST API."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL for API. Defaults to API_URL env var or http://localhost:8000
        """
        self.base_url = base_url or os.environ.get("API_URL", "http://localhost:8000")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_status(self) -> dict:
        """
        Get API status.
        
        Returns:
            Status information including health and version
        """
        response = self.session.get(f"{self.base_url}/api/v1/status")
        response.raise_for_status()
        return response.json()
    
    def get_stats(self) -> dict:
        """
        Get library statistics.
        
        Returns:
            Counts for documents, entities, events, locations, parsers, watcher status
        """
        response = self.session.get(f"{self.base_url}/api/v1/stats")
        response.raise_for_status()
        return response.json()
    
    def ask_question(self, question: str, options: Optional[dict] = None) -> dict:
        """
        Ask a question about the library.
        
        Args:
            question: The natural language question
            options: Optional dict with include_evidence, include_trace, max_evidence_items
        
        Returns:
            Question response with answer, evidence, and trace
        """
        payload = {"question": question}
        if options:
            payload["options"] = options
        
        response = self.session.post(
            f"{self.base_url}/api/v1/questions",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def get_question(self, question_id: str) -> dict:
        """
        Get a previously asked question.
        
        Args:
            question_id: The ID of the question to retrieve
        
        Returns:
            Question history with answer, evidence, and trace
        """
        response = self.session.get(f"{self.base_url}/api/v1/questions/{question_id}")
        response.raise_for_status()
        return response.json()
    
    def get_timeline(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        entity: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50
    ) -> dict:
        """
        Get timeline of events.
        
        Args:
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)
            entity: Filter by entity name
            event_type: Filter by event type
            limit: Maximum number of results
        
        Returns:
            Timeline events with pagination info
        """
        params = {"limit": limit}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if entity:
            params["entity"] = entity
        if event_type:
            params["event_type"] = event_type
        
        response = self.session.get(
            f"{self.base_url}/api/v1/timeline",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> bool:
        """
        Check if API is healthy.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False


# Singleton instance for convenience
_client: Optional[LibrarianAPIClient] = None


def get_client(base_url: Optional[str] = None) -> LibrarianAPIClient:
    """
    Get or create the API client singleton.
    
    Args:
        base_url: Optional base URL to use
    
    Returns:
        LibrarianAPIClient instance
    """
    global _client
    if _client is None:
        _client = LibrarianAPIClient(base_url)
    return _client
