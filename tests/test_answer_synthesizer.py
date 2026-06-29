import json
from core.answer_synthesizer import synthesize_answer


def test_location_query():
    """Where was I on January 1 2026?"""
    evidence_package = {
        "question": "Where was I on January 1 2026?",
        "intent": "location_query",
        "evidence": {
            "documents": [],
            "entities": [],
            "events": [
                {"timestamp": "2026-01-01", "event_type": "photo_capture", "description": "Photo taken"}
            ],
            "locations": [
                {"name": "Manila", "latitude": 14.5995, "longitude": 120.9842, "source": "photo.jpg"}
            ],
            "relationships": []
        }
    }
    return synthesize_answer("Where was I on January 1 2026?", evidence_package)


def test_timeline_query():
    """What happened in January 2026?"""
    evidence_package = {
        "question": "What happened in January 2026?",
        "intent": "timeline_query",
        "evidence": {
            "documents": [
                {"path": "meeting_notes.md", "text": "Notes"}
            ],
            "entities": [],
            "events": [
                {"timestamp": "2026-01-01", "event_type": "meeting", "description": "Q1 Planning meeting"},
                {"timestamp": "2026-01-15", "event_type": "purchase", "description": "Equipment bought"},
                {"timestamp": "2026-01-20", "event_type": "review", "description": "Code review completed"}
            ],
            "locations": [],
            "relationships": []
        }
    }
    return synthesize_answer("What happened in January 2026?", evidence_package)


def test_entity_query():
    """Show me everything related to HONOR BRP-NX1"""
    evidence_package = {
        "question": "Show me everything related to HONOR BRP-NX1",
        "intent": "entity_query",
        "evidence": {
            "documents": [
                {"path": "IMG_20260101.jpg", "text": "Photo from device"}
            ],
            "entities": [
                {"type": "device", "value": "HONOR BRP-NX1", "source": "IMG_20260101.jpg"}
            ],
            "events": [
                {"timestamp": "2026-01-01", "event_type": "photo", "description": "Photo captured"}
            ],
            "locations": [
                {"name": "Makati", "source": "IMG_20260101.jpg"}
            ],
            "relationships": []
        }
    }
    return synthesize_answer("Show me everything related to HONOR BRP-NX1", evidence_package)


def test_profile_query():
    """Give me the profile of ABC Corp"""
    evidence_package = {
        "question": "Give me the profile of ABC Corp",
        "intent": "profile_query",
        "evidence": {
            "documents": [
                {"path": "contract.pdf", "text": "Contract with ABC Corp"}
            ],
            "entities": [
                {"type": "organization", "value": "ABC Corp", "source": "contract.pdf"},
                {"type": "person", "value": "John Smith", "source": "contract.pdf"}
            ],
            "events": [
                {"timestamp": "2026-01-15", "event_type": "contract_signed", "description": "Contract signed"}
            ],
            "locations": [
                {"name": "Makati", "source": "contract.pdf"}
            ],
            "relationships": [
                {"from": "John Smith", "to": "ABC Corp", "type": "works_for", "source": "contract.pdf"}
            ]
        }
    }
    return synthesize_answer("Give me the profile of ABC Corp", evidence_package)


def test_event_query():
    """When did inverter failures begin?"""
    evidence_package = {
        "question": "When did inverter failures begin?",
        "intent": "event_query",
        "evidence": {
            "documents": [],
            "entities": [],
            "events": [
                {"timestamp": "2026-01-10", "event_type": "failure", "description": "First inverter failure reported"},
                {"timestamp": "2026-01-15", "event_type": "failure", "description": "Second inverter failure"}
            ],
            "locations": [],
            "relationships": []
        }
    }
    return synthesize_answer("When did inverter failures begin?", evidence_package)


def test_no_evidence():
    """Test when no evidence is available"""
    evidence_package = {
        "question": "Where was I in 2020?",
        "intent": "location_query",
        "evidence": {
            "documents": [],
            "entities": [],
            "events": [],
            "locations": [],
            "relationships": []
        }
    }
    return synthesize_answer("Where was I in 2020?", evidence_package)


if __name__ == "__main__":
    tests = [
        ("location_query", "Where was I on January 1 2026?", test_location_query),
        ("timeline_query", "What happened in January 2026?", test_timeline_query),
        ("entity_query", "Show me everything related to HONOR BRP-NX1", test_entity_query),
        ("profile_query", "Give me the profile of ABC Corp", test_profile_query),
        ("event_query", "When did inverter failures begin?", test_event_query),
        ("no_evidence", "Where was I in 2020?", test_no_evidence)
    ]
    
    for name, question, test_fn in tests:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print('='*60)
        result = test_fn()
        print(f"Answer:\n{result['answer']}")
        print(f"\nConfidence: {result['confidence']}")
        print(f"Evidence used: {result['evidence_used']}")