import json
from core.evidence_builder import build_evidence, EvidenceBuilder


class MockBackend:
    def __init__(self):
        self.documents = [
            {'path': 'IMG_20260101_122510.jpg', 'structured_data': {'timestamp': '2026:01:01 12:25:10', 'camera_make': 'HONOR', 'camera_model': 'BRP-NX1'}},
            {'path': 'meeting_notes.md', 'text': 'Meeting on January 1 2026'}
        ]
        self.entities = [
            {'type': 'person', 'value': 'John Smith'},
            {'type': 'organization', 'value': 'ABC Corp'}
        ]
        self.events = [
            {'timestamp': '2026-01-01', 'event_type': 'meeting', 'description': 'Meeting on Jan 1'}
        ]
        self.locations = [
            {'name': 'Manila', 'latitude': 14.5995, 'longitude': 120.9842}
        ]

    def search_documents(self, query):
        return [d for d in self.documents if query.lower() in str(d).lower()]

    def search_entities(self, entity_type=None, value=None):
        return self.entities

    def search_events(self, timestamp=None, event_type=None):
        return self.events

    def search_locations(self, location_name=None):
        return self.locations


backend = MockBackend()

# Test 1: "Where was I on January 1 2026?"
planner_result_1 = {
    'type': 'events',
    'intent': 'location_query',
    'timestamp': '2026-01-01'
}
result_1 = build_evidence("Where was I on January 1 2026?", planner_result_1, backend)
print("Question: Where was I on January 1 2026?")
print(json.dumps(result_1, indent=2))
print()

# Test 2: "Show me everything related to HONOR BRP-NX1"
planner_result_2 = {
    'type': 'documents',
    'intent': 'device_query',
    'query': 'HONOR BRP-NX1'
}
result_2 = build_evidence("Show me everything related to HONOR BRP-NX1", planner_result_2, backend)
print("Question: Show me everything related to HONOR BRP-NX1")
print(json.dumps(result_2, indent=2))
print()

# Test 3: "What happened in January 2026?"
planner_result_3 = {
    'type': 'events',
    'intent': 'timeline_query',
    'retrieve_locations': True
}
result_3 = build_evidence("What happened in January 2026?", planner_result_3, backend)
print("Question: What happened in January 2026?")
print(json.dumps(result_3, indent=2))