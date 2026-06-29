from core.evidence_trace import build_trace


def test_evidence_trace():
    """Test evidence trace building."""
    
    # Mock evidence package with scores and reasons from evidence_ranker
    evidence_package = {
        "documents": [
            {"path": "report.pdf", "score": 20, "reason": "keyword_match"},
            {"path": "abc_contract.pdf", "score": 100, "reason": "exact_entity_match"},
            {"path": "notes.txt", "score": 20, "reason": "keyword_match"}
        ],
        "entities": [
            {"value": "John Smith", "source": "notes.txt", "score": 40, "reason": "regex_extraction"},
            {"value": "ABC Corp", "source": "contract.pdf", "score": 100, "reason": "explicit_metadata"},
            {"value": "Manila", "source": "data.json", "score": 70, "reason": "structured_extraction"}
        ],
        "events": [
            {"description": "Photo taken", "source": "IMG_20260101.jpg", "score": 100, "reason": "photo_timestamp"},
            {"description": "EXIF event", "source": "IMG_20260115.jpg", "score": 90, "reason": "exif_timestamp"},
            {"description": "Filesystem event", "source": "notes.txt", "score": 30, "reason": "filesystem_timestamp"}
        ],
        "locations": [
            {"name": "Manila", "source": "IMG_20260101.jpg", "score": 100, "reason": "gps_exif"},
            {"name": "Makati", "source": "data.json", "score": 90, "reason": "gps_phone"},
            {"name": "Quezon City", "source": "notes.txt", "score": 40, "reason": "text_location"}
        ],
        "relationships": [
            {"from": "John", "to": "ABC Corp", "type": "works_for", "source": "contract.pdf", "score": 100, "reason": "explicit_relationship"},
            {"from": "ABC Corp", "to": "Manila", "type": "located_in", "source": "notes.txt", "score": 50, "reason": "inferred_relationship"}
        ]
    }
    
    trace = build_trace(evidence_package)
    
    print("="*60)
    print("EVIDENCE TRACE")
    print("="*60)
    print()
    
    for i, entry in enumerate(trace, 1):
        print(f"{i}. [{entry['type']}] {entry['source']}")
        print(f"   Score: {entry['score']} | Reason: {entry['reason']}")
        print()
    
    print("="*60)
    print("VERIFICATION")
    print("="*60)
    
    # Verify sorting
    scores = [e['score'] for e in trace]
    is_sorted = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
    print(f"  Sorted by score (descending): {is_sorted}")
    print(f"  Total trace entries: {len(trace)}")
    print(f"  Score range: {min(scores)} - {max(scores)}")


if __name__ == "__main__":
    test_evidence_trace()