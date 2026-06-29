import json
from core.query_executor import execute_query


class MockBackend:
    """Mock storage backend with date-filtered data."""
    
    def __init__(self):
        self.documents = [
            {'path': 'IMG_20260101_122510.jpg', 'text': 'Photo from Manila on Jan 1 2026', 'structured_data': {'timestamp': '2026:01:01 12:25:10'}},
            {'path': 'IMG_20260115_090000.jpg', 'text': 'Site visit at Marikina Jan 15 2026', 'structured_data': {'timestamp': '2026:01:15 09:00:00'}},
            {'path': 'IMG_20260201_140000.jpg', 'text': 'Maintenance visit Feb 1 2026', 'structured_data': {'timestamp': '2026:02:01 14:00:00'}},
            {'path': 'inverter_manual.pdf', 'text': 'Manual for HONOR BRP-NX1', 'structured_data': {}},
            {'path': 'abc_contract.pdf', 'text': 'Contract with ABC Corp', 'structured_data': {}}
        ]
        self.entities = [
            {'type': 'device', 'value': 'HONOR BRP-NX1', 'source': 'inverter_manual.pdf'},
            {'type': 'organization', 'value': 'ABC Corp', 'source': 'abc_contract.pdf'}
        ]
        self.events = [
            {'timestamp': '2026-01-01', 'event_type': 'photo', 'description': 'Photo taken at Manila'},
            {'timestamp': '2026-01-15', 'event_type': 'site_visit', 'description': 'Site visit at Marikina'},
            {'timestamp': '2026-02-01', 'event_type': 'maintenance', 'description': 'Maintenance visit'}
        ]
        self.locations = [
            {'name': 'Manila', 'latitude': 14.5995, 'longitude': 120.9842, 'source': 'IMG_20260101_122510.jpg', 'timestamp': '2026-01-01'},
            {'name': 'Marikina', 'latitude': 14.6389, 'longitude': 121.1156, 'source': 'IMG_20260115_090000.jpg', 'timestamp': '2026-01-15'},
            {'name': 'Quezon City', 'latitude': 14.6760, 'longitude': 121.0437, 'source': 'IMG_20260201_140000.jpg', 'timestamp': '2026-02-01'}
        ]
        self.relationships = [
            {'from': 'ABC Corp', 'to': 'Manila', 'type': 'located_in', 'source': 'abc_contract.pdf'},
            {'from': 'ABC Corp', 'to': 'Marikina', 'type': 'operates_in', 'source': 'abc_contract.pdf'},
            {'from': 'HONOR BRP-NX1', 'to': 'Manila', 'type': 'located_in', 'source': 'inverter_manual.pdf'}
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


def display_evidence(evidence):
    """Display evidence in a readable format."""
    print(f"  Documents: {len(evidence['documents'])} found")
    for d in evidence['documents']:
        print(f"    - {d.get('path')}")
    print(f"  Entities: {len(evidence['entities'])} found")
    for e in evidence['entities']:
        print(f"    - {e.get('value')} ({e.get('type')})")
    print(f"  Events: {len(evidence['events'])} found")
    for e in evidence['events']:
        print(f"    - {e.get('timestamp')} [{e.get('event_type')}]: {e.get('description')}")
    print(f"  Locations: {len(evidence['locations'])} found")
    for l in evidence['locations']:
        print(f"    - {l.get('name')}")
    print(f"  Relationships: {len(evidence['relationships'])} found")
    for r in evidence['relationships']:
        print(f"    - {r.get('from')} {r.get('type')} {r.get('to')}")


if __name__ == "__main__":
    backend = MockBackend()
    
    # Test 1: Location query with date filter
    print("="*60)
    print("Test 1: Where was I on January 1 2026?")
    print("="*60)
    plan = {
        "intent": "location_query",
        "required_evidence": ["events", "locations", "documents"],
        "filters": {"date": "January 1 2026"}
    }
    result = execute_query(plan, backend)
    display_evidence(result['evidence'])
    
    # Test 2: Timeline query with month filter
    print("\n" + "="*60)
    print("Test 2: What happened in January 2026?")
    print("="*60)
    plan = {
        "intent": "timeline_query",
        "required_evidence": ["events", "documents"],
        "filters": {"month": "2026-01"}
    }
    result = execute_query(plan, backend)
    display_evidence(result['evidence'])
    
    # Test 3: Entity query with entity filter
    print("\n" + "="*60)
    print("Test 3: Show me everything related to HONOR BRP-NX1")
    print("="*60)
    plan = {
        "intent": "entity_query",
        "required_evidence": ["entities", "documents", "events"],
        "filters": {"entity": "HONOR BRP-NX1"}
    }
    result = execute_query(plan, backend)
    display_evidence(result['evidence'])
    
    # Test 4: Profile query with entity filter
    print("\n" + "="*60)
    print("Test 4: Give me the profile of ABC Corp")
    print("="*60)
    plan = {
        "intent": "profile_query",
        "required_evidence": ["entities", "relationships", "events", "documents"],
        "filters": {"entity": "ABC Corp"}
    }
    result = execute_query(plan, backend)
    display_evidence(result['evidence'])