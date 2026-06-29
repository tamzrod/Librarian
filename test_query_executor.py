import json
from core.query_executor import execute_query


class MockBackend:
    """Mock storage backend for testing."""
    
    def __init__(self):
        self.documents = [
            {'path': 'IMG_20260101_122510.jpg', 'text': 'Photo from Manila on Jan 1 2026', 'structured_data': {'timestamp': '2026:01:01 12:25:10'}},
            {'path': 'meeting_notes.md', 'text': 'Meeting notes for ABC Corp', 'structured_data': {}},
            {'path': 'report_2026.pdf', 'text': 'Annual report for 2026', 'structured_data': {}}
        ]
        self.entities = [
            {'type': 'organization', 'value': 'ABC Corp', 'source': 'meeting_notes.md'},
            {'type': 'person', 'value': 'John Smith', 'source': 'report_2026.pdf'},
            {'type': 'device', 'value': 'HONOR BRP-NX1', 'source': 'IMG_20260101_122510.jpg'}
        ]
        self.events = [
            {'timestamp': '2026-01-01', 'event_type': 'photo_capture', 'description': 'Photo taken in Manila'},
            {'timestamp': '2026-01-15', 'event_type': 'meeting', 'description': 'Meeting with ABC Corp'},
            {'timestamp': '2026-02-01', 'event_type': 'report', 'description': 'Annual report published'}
        ]
        self.locations = [
            {'name': 'Manila', 'latitude': 14.5995, 'longitude': 120.9842, 'source': 'IMG_20260101_122510.jpg'},
            {'name': 'Makati', 'latitude': 14.5547, 'longitude': 121.0244, 'source': 'meeting_notes.md'}
        ]
        self.relationships = [
            {'from': 'John Smith', 'to': 'ABC Corp', 'type': 'works_for', 'source': 'report_2026.pdf'},
            {'from': 'ABC Corp', 'to': 'Manila', 'type': 'located_in', 'source': 'meeting_notes.md'}
        ]
    
    def search_documents(self, query=""):
        if not query:
            return self.documents
        return [d for d in self.documents if query.lower() in str(d).lower()]
    
    def search_entities(self, entity_type=None, value=None):
        results = self.entities
        if entity_type:
            results = [e for e in results if e.get('type') == entity_type]
        if value:
            results = [e for e in results if value.lower() in e.get('value', '').lower()]
        return results
    
    def search_events(self, timestamp=None, event_type=None):
        results = self.events
        if timestamp:
            results = [e for e in results if timestamp in e.get('timestamp', '')]
        if event_type:
            results = [e for e in results if e.get('event_type') == event_type]
        return results
    
    def search_locations(self, location_name=None):
        if not location_name:
            return self.locations
        return [l for l in self.locations if location_name.lower() in l.get('name', '').lower()]
    
    def search_relationships(self, filters=None):
        return self.relationships


def test_location_query():
    """Test: Where was I on January 1 2026?"""
    plan = {
        "intent": "location_query",
        "required_evidence": ["events", "locations", "documents"],
        "filters": {"date": "January 1 2026"}
    }
    return execute_query(plan, MockBackend())


def test_timeline_query():
    """Test: What happened in January 2026?"""
    plan = {
        "intent": "timeline_query",
        "required_evidence": ["events", "documents"],
        "filters": {"month": "2026-01"}
    }
    return execute_query(plan, MockBackend())


def test_entity_query():
    """Test: Show me everything related to ABC Corp"""
    plan = {
        "intent": "entity_query",
        "required_evidence": ["entities", "documents", "events"],
        "filters": {"entity": "ABC Corp"}
    }
    return execute_query(plan, MockBackend())


def test_profile_query():
    """Test: Give me the profile of ABC Corp"""
    plan = {
        "intent": "profile_query",
        "required_evidence": ["entities", "relationships", "events", "documents"],
        "filters": {"entity": "ABC Corp"}
    }
    return execute_query(plan, MockBackend())


if __name__ == "__main__":
    tests = [
        ("location_query", test_location_query),
        ("timeline_query", test_timeline_query),
        ("entity_query", test_entity_query),
        ("profile_query", test_profile_query)
    ]
    
    for name, test_fn in tests:
        print(f"\n{'='*60}")
        print(f"Test: {name}")
        print('='*60)
        result = test_fn()
        print(json.dumps(result, indent=2))