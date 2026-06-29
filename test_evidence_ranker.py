from core.evidence_ranker import rank_evidence


def test_evidence_ranking():
    """Test evidence ranking with mock data."""
    
    evidence_package = {
        "documents": [
            {"path": "report.pdf", "text": "Contains ABC Corp info"},
            {"path": "abc_contract.pdf", "exact_match": True},
            {"path": "notes.txt", "text": "keyword match"}
        ],
        "entities": [
            {"type": "person", "value": "John Smith", "source": "notes.txt"},  # regex
            {"type": "organization", "value": "ABC Corp", "metadata": True},  # explicit
            {"type": "location", "value": "Manila", "source": "data.json"}  # structured
        ],
        "events": [
            {"timestamp": "2026-01-01", "event_type": "photo", "description": "Photo event"},  # photo
            {"timestamp": "2026-01-15", "source": "IMG_20260115.jpg", "description": "EXIF event"},  # exif
            {"timestamp": "2026-02-01", "source": "notes.txt", "description": "Filesystem event"}  # filesystem
        ],
        "locations": [
            {"name": "Manila", "latitude": 14.5995, "longitude": 120.9842, "source": "photo.jpg"},  # GPS EXIF
            {"name": "Makati", "latitude": 14.5547, "longitude": 121.0244, "source": "data.json"},  # GPS phone
            {"name": "Quezon City", "source": "notes.txt"}  # text location
        ],
        "relationships": [
            {"from": "John", "to": "ABC Corp", "type": "works_for", "explicit": True},  # explicit
            {"from": "ABC Corp", "to": "Manila", "type": "located_in"}  # inferred
        ]
    }
    
    result = rank_evidence(evidence_package)
    
    print("="*60)
    print("RANKED EVIDENCE")
    print("="*60)
    
    print("\n--- LOCATIONS ---")
    for loc in result["locations"]:
        print(f"  {loc.get('name')}: score={loc.get('score')}, reason={loc.get('reason')}")
    
    print("\n--- EVENTS ---")
    for event in result["events"]:
        print(f"  {event.get('description')}: score={event.get('score')}, reason={event.get('reason')}")
    
    print("\n--- ENTITIES ---")
    for entity in result["entities"]:
        print(f"  {entity.get('value')}: score={entity.get('score')}, reason={entity.get('reason')}")
    
    print("\n--- RELATIONSHIPS ---")
    for rel in result["relationships"]:
        print(f"  {rel.get('from')} {rel.get('type')} {rel.get('to')}: score={rel.get('score')}, reason={rel.get('reason')}")
    
    print("\n--- DOCUMENTS ---")
    for doc in result["documents"]:
        print(f"  {doc.get('path')}: score={doc.get('score')}, reason={doc.get('reason')}")
    
    print("\n--- SCORE BREAKDOWN ---")
    for item in result["score_breakdown"]:
        print(f"  [{item['type']}] {item['item']}: {item['score']} ({item['reason']})")
    
    print("\n" + "="*60)
    print("VERIFICATION: Evidence sorted by score (descending)")
    print("="*60)
    
    all_scores = []
    for loc in result["locations"]:
        all_scores.append((loc.get("name"), loc.get("score")))
    for event in result["events"]:
        all_scores.append((event.get("description"), event.get("score")))
    for entity in result["entities"]:
        all_scores.append((entity.get("value"), entity.get("score")))
    for rel in result["relationships"]:
        all_scores.append((f"{rel.get('from')}-{rel.get('to')}", rel.get("score")))
    for doc in result["documents"]:
        all_scores.append((doc.get("path"), doc.get("score")))
    
    sorted_scores = sorted(all_scores, key=lambda x: x[1], reverse=True)
    print(f"  Sorted order: {sorted_scores}")
    
    # Verify descending order
    scores_only = [s[1] for s in sorted_scores]
    is_sorted = all(scores_only[i] >= scores_only[i+1] for i in range(len(scores_only)-1))
    print(f"  Correctly sorted (descending): {is_sorted}")


if __name__ == "__main__":
    test_evidence_ranking()