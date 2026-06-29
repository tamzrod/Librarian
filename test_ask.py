import json
from core.ask import ask


class MockBackend:
    """Mock storage backend for testing."""
    
    def __init__(self):
        self.documents = [
            {'path': 'IMG_20260101_122510.jpg', 'text': 'Photo from Manila on Jan 1 2026', 'structured_data': {'timestamp': '2026:01:01 12:25:10'}},
            {'path': 'inverter_manual.pdf', 'text': 'Inverter maintenance manual for HONOR BRP-NX1', 'structured_data': {}},
            {'path': 'abc_contract.pdf', 'text': 'Contract with ABC Corp', 'structured_data': {}}
        ]
        self.entities = [
            {'type': 'organization', 'value': 'ABC Corp', 'source': 'abc_contract.pdf'},
            {'type': 'device', 'value': 'HONOR BRP-NX1', 'source': 'inverter_manual.pdf'}
        ]
        self.events = [
            {'timestamp': '2026-01-01', 'event_type': 'photo_capture', 'description': 'Photo taken in Manila'},
            {'timestamp': '2026-01-15', 'event_type': 'site_visit', 'description': 'Site visit at Marikina'}
        ]
        self.locations = [
            {'name': 'Manila', 'latitude': 14.5995, 'longitude': 120.9842, 'source': 'IMG_20260101_122510.jpg'},
            {'name': 'Marikina', 'latitude': 14.6389, 'longitude': 121.1156, 'source': 'abc_contract.pdf'}
        ]
        self.relationships = [
            {'from': 'ABC Corp', 'to': 'Manila', 'type': 'located_in', 'source': 'abc_contract.pdf'},
            {'from': 'Rod', 'to': 'ABC Corp', 'type': 'works_for', 'source': 'abc_contract.pdf'}
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


def display_result(result):
    """Display a query result in a formatted way."""
    print(f"\n{'='*50}")
    print(f"Question: {result['question']}")
    print('='*50)
    
    print("\nPlan:")
    print(json.dumps(result['plan'], indent=2))
    
    print("\nEvidence:")
    print(json.dumps(result['evidence'], indent=2))
    
    print("\nAnswer:")
    print(result['answer']['answer'])
    print(f"\nConfidence: {result['answer']['confidence']}")


if __name__ == "__main__":
    backend = MockBackend()
    
    test_questions = [
        "Where was I on January 1 2026?",
        "What happened in January 2026?",
        "Show me everything related to HONOR BRP-NX1",
        "Give me the profile of ABC Corp",
        "When did site visits begin?"
    ]
    
    for question in test_questions:
        result = ask(question, backend)
        display_result(result)