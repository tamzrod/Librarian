def build_trace(evidence_package):
    """
    Provide explainability for every answer by building a trace of evidence sources.
    
    Args:
        evidence_package: Dict with documents, entities, events, locations, relationships
    
    Returns:
        List of trace entries sorted by score (descending)
    """
    trace = []
    
    # Extract documents
    for doc in evidence_package.get("documents", []):
        trace.append({
            "type": "document",
            "source": doc.get("path", "unknown"),
            "score": doc.get("score", 0),
            "reason": doc.get("reason", "unknown")
        })
    
    # Extract entities
    for entity in evidence_package.get("entities", []):
        trace.append({
            "type": "entity",
            "source": entity.get("source", "unknown"),
            "score": entity.get("score", 0),
            "reason": entity.get("reason", "unknown")
        })
    
    # Extract events
    for event in evidence_package.get("events", []):
        trace.append({
            "type": "event",
            "source": event.get("source", "unknown"),
            "score": event.get("score", 0),
            "reason": event.get("reason", "unknown")
        })
    
    # Extract locations
    for location in evidence_package.get("locations", []):
        trace.append({
            "type": "location",
            "source": location.get("source", "unknown"),
            "score": location.get("score", 0),
            "reason": location.get("reason", "unknown")
        })
    
    # Extract relationships
    for relationship in evidence_package.get("relationships", []):
        trace.append({
            "type": "relationship",
            "source": relationship.get("source", "unknown"),
            "score": relationship.get("score", 0),
            "reason": relationship.get("reason", "unknown")
        })
    
    # Sort by score descending
    trace.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return trace