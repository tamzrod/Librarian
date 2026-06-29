def rank_evidence(evidence_package):
    """
    Rank evidence by reliability and relevance before synthesis.
    
    Args:
        evidence_package: Dict with documents, entities, events, locations, relationships
    
    Returns:
        Dict with ranked evidence and score breakdown
    """
    documents = evidence_package.get("documents", [])
    entities = evidence_package.get("entities", [])
    events = evidence_package.get("events", [])
    locations = evidence_package.get("locations", [])
    relationships = evidence_package.get("relationships", [])
    
    score_breakdown = []
    
    # Rank each evidence type
    ranked_documents = _rank_documents(documents, score_breakdown)
    ranked_entities = _rank_entities(entities, score_breakdown)
    ranked_events = _rank_events(events, score_breakdown)
    ranked_locations = _rank_locations(locations, score_breakdown)
    ranked_relationships = _rank_relationships(relationships, score_breakdown)
    
    return {
        "documents": ranked_documents,
        "entities": ranked_entities,
        "events": ranked_events,
        "locations": ranked_locations,
        "relationships": ranked_relationships,
        "score_breakdown": score_breakdown
    }


def _rank_locations(locations, score_breakdown):
    """Rank locations by reliability."""
    scored = []
    
    for loc in locations:
        score = 0
        reason = ""
        
        # Check for GPS from photo metadata (highest reliability)
        if loc.get("latitude") is not None and loc.get("longitude") is not None:
            if loc.get("source", "").lower().endswith(('.jpg', '.jpeg', '.png')):
                score = 100
                reason = "gps_exif"
            else:
                score = 90
                reason = "gps_phone"
        # Location extracted from text (lower reliability)
        elif loc.get("name"):
            score = 40
            reason = "text_location"
        
        if score > 0:
            scored_item = {**loc, "score": score, "reason": reason}
            scored.append(scored_item)
            score_breakdown.append({
                "type": "location",
                "item": loc.get("name", "unknown"),
                "score": score,
                "reason": reason
            })
    
    # Sort descending by score
    scored.sort(key=lambda x: x.get("score", 0), reverse=True)
    return scored


def _rank_events(events, score_breakdown):
    """Rank events by reliability."""
    scored = []
    
    for event in events:
        score = 0
        reason = ""
        
        # Photo timestamp (highest reliability)
        if event.get("event_type") == "photo" and event.get("timestamp"):
            score = 100
            reason = "photo_timestamp"
        # EXIF timestamp
        elif event.get("source", "").lower().endswith(('.jpg', '.jpeg', '.png')):
            score = 90
            reason = "exif_timestamp"
        # Filesystem timestamp (lower reliability)
        elif event.get("source"):
            score = 30
            reason = "filesystem_timestamp"
        
        if score > 0:
            scored_item = {**event, "score": score, "reason": reason}
            scored.append(scored_item)
            score_breakdown.append({
                "type": "event",
                "item": event.get("description", "unknown"),
                "score": score,
                "reason": reason
            })
    
    # Sort descending by score
    scored.sort(key=lambda x: x.get("score", 0), reverse=True)
    return scored


def _rank_entities(entities, score_breakdown):
    """Rank entities by reliability."""
    scored = []
    
    for entity in entities:
        score = 0
        reason = ""
        
        # Explicit metadata (highest reliability)
        if entity.get("metadata") or entity.get("structured"):
            score = 100
            reason = "explicit_metadata"
        # Structured document extraction
        elif entity.get("source", "").lower().endswith(('.json', '.yaml', '.toml', '.xml')):
            score = 70
            reason = "structured_extraction"
        # Regex extraction (lower reliability)
        else:
            score = 40
            reason = "regex_extraction"
        
        if score > 0:
            scored_item = {**entity, "score": score, "reason": reason}
            scored.append(scored_item)
            score_breakdown.append({
                "type": "entity",
                "item": entity.get("value", "unknown"),
                "score": score,
                "reason": reason
            })
    
    # Sort descending by score
    scored.sort(key=lambda x: x.get("score", 0), reverse=True)
    return scored


def _rank_relationships(relationships, score_breakdown):
    """Rank relationships by reliability."""
    scored = []
    
    for rel in relationships:
        score = 0
        reason = ""
        
        # Explicit relationship (highest reliability)
        if rel.get("explicit") or rel.get("metadata"):
            score = 100
            reason = "explicit_relationship"
        # Inferred relationship (lower reliability)
        else:
            score = 50
            reason = "inferred_relationship"
        
        if score > 0:
            scored_item = {**rel, "score": score, "reason": reason}
            scored.append(scored_item)
            score_breakdown.append({
                "type": "relationship",
                "item": f"{rel.get('from', '')} {rel.get('type', '')} {rel.get('to', '')}",
                "score": score,
                "reason": reason
            })
    
    # Sort descending by score
    scored.sort(key=lambda x: x.get("score", 0), reverse=True)
    return scored


def _rank_documents(documents, score_breakdown):
    """Rank documents by relevance."""
    scored = []
    
    for doc in documents:
        score = 0
        reason = ""
        
        # Exact entity match (highest relevance)
        if doc.get("exact_match"):
            score = 100
            reason = "exact_entity_match"
        # Filename match
        elif doc.get("filename_match"):
            score = 60
            reason = "filename_match"
        # Keyword match (lower relevance)
        else:
            score = 20
            reason = "keyword_match"
        
        if score > 0:
            scored_item = {**doc, "score": score, "reason": reason}
            scored.append(scored_item)
            score_breakdown.append({
                "type": "document",
                "item": doc.get("path", "unknown"),
                "score": score,
                "reason": reason
            })
    
    # Sort descending by score
    scored.sort(key=lambda x: x.get("score", 0), reverse=True)
    return scored