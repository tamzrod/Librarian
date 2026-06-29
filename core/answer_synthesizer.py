def synthesize_answer(question, evidence_package):
    """
    Generate a human-readable answer from an evidence package.
    
    Args:
        question: The original question
        evidence_package: Dict with intent and evidence
    
    Returns:
        Dict with answer, confidence, and evidence_used
    """
    intent = evidence_package.get("intent", "unknown")
    evidence = evidence_package.get("evidence", {})
    
    evidence_used = []
    answer = ""
    confidence = 0.0
    
    if intent == "location_query":
        answer, evidence_used = _synthesize_location(evidence)
        confidence = _calculate_confidence(evidence, ["locations", "events"])
    
    elif intent == "timeline_query":
        answer, evidence_used = _synthesize_timeline(evidence)
        confidence = _calculate_confidence(evidence, ["events"])
    
    elif intent == "entity_query":
        answer, evidence_used = _synthesize_entity(evidence)
        confidence = _calculate_confidence(evidence, ["entities"])
    
    elif intent == "profile_query":
        answer, evidence_used = _synthesize_profile(evidence)
        confidence = _calculate_confidence(evidence, ["entities", "relationships", "events"])
    
    elif intent == "event_query":
        answer, evidence_used = _synthesize_event(evidence)
        confidence = _calculate_confidence(evidence, ["events"])
    
    elif intent == "document_query":
        answer, evidence_used = _synthesize_document(evidence)
        confidence = _calculate_confidence(evidence, ["documents"])
    
    else:
        answer = "Unable to determine question intent."
        confidence = 0.0
    
    return {
        "answer": answer,
        "confidence": confidence,
        "evidence_used": evidence_used
    }


def _synthesize_location(evidence):
    """Synthesize answer for location queries."""
    locations = evidence.get("locations", [])
    events = evidence.get("events", [])
    
    if not locations and not events:
        return "No matching evidence was found.", []
    
    parts = []
    evidence_used = []
    
    if locations:
        loc_names = [l.get("name", "Unknown") for l in locations]
        parts.append(f"You were at: {', '.join(loc_names)}")
        evidence_used.extend([f"location:{l.get('name')}" for l in locations])
    
    if events:
        for event in events:
            ts = event.get("timestamp", "Unknown date")
            desc = event.get("description", "Event occurred")
            parts.append(f"- {ts}: {desc}")
            evidence_used.append(f"event:{ts}")
    
    return "\n".join(parts), evidence_used


def _synthesize_timeline(evidence):
    """Synthesize answer for timeline queries."""
    events = evidence.get("events", [])
    documents = evidence.get("documents", [])
    
    if not events and not documents:
        return "No matching evidence was found.", []
    
    evidence_used = []
    parts = []
    
    # Sort events chronologically
    sorted_events = sorted(events, key=lambda x: x.get("timestamp", ""))
    
    if sorted_events:
        parts.append("Events in this period:")
        for event in sorted_events:
            ts = event.get("timestamp", "Unknown")
            etype = event.get("event_type", "event")
            desc = event.get("description", "")
            parts.append(f"- {ts} [{etype}]: {desc}")
            evidence_used.append(f"event:{ts}")
    
    if documents:
        parts.append(f"\n{len(documents)} document(s) are relevant.")
        evidence_used.extend([f"doc:{d.get('path', 'unknown')}" for d in documents])
    
    return "\n".join(parts), evidence_used


def _synthesize_entity(evidence):
    """Synthesize answer for entity queries."""
    entities = evidence.get("entities", [])
    documents = evidence.get("documents", [])
    events = evidence.get("events", [])
    
    if not entities and not documents and not events:
        return "No matching evidence was found.", []
    
    evidence_used = []
    parts = []
    
    if entities:
        parts.append("Matching entities:")
        for entity in entities:
            etype = entity.get("type", "entity")
            value = entity.get("value", "Unknown")
            source = entity.get("source", "")
            parts.append(f"- {value} ({etype})")
            evidence_used.append(f"entity:{value}")
    
    if documents:
        parts.append(f"\n{len(documents)} document(s) contain this entity.")
        evidence_used.extend([f"doc:{d.get('path', 'unknown')}" for d in documents])
    
    if events:
        parts.append(f"\n{len(events)} event(s) related to this entity.")
        evidence_used.extend([f"event:{e.get('timestamp', '')}" for e in events])
    
    return "\n".join(parts), evidence_used


def _synthesize_profile(evidence):
    """Synthesize answer for profile queries."""
    entities = evidence.get("entities", [])
    relationships = evidence.get("relationships", [])
    events = evidence.get("events", [])
    documents = evidence.get("documents", [])
    
    if not entities and not relationships and not events and not documents:
        return "No matching evidence was found.", []
    
    evidence_used = []
    parts = []
    
    if entities:
        parts.append("Entities:")
        for entity in entities:
            value = entity.get("value", "Unknown")
            etype = entity.get("type", "entity")
            parts.append(f"- {value} ({etype})")
            evidence_used.append(f"entity:{value}")
    
    if relationships:
        parts.append("\nRelationships:")
        for rel in relationships:
            from_ent = rel.get("from", "")
            to_ent = rel.get("to", "")
            rtype = rel.get("type", "")
            parts.append(f"- {from_ent} {rtype} {to_ent}")
            evidence_used.append(f"rel:{rtype}")
    
    if events:
        parts.append(f"\n{len(events)} event(s) associated.")
        evidence_used.extend([f"event:{e.get('timestamp', '')}" for e in events])
    
    if documents:
        parts.append(f"\n{len(documents)} document(s) available.")
        evidence_used.extend([f"doc:{d.get('path', 'unknown')}" for d in documents])
    
    return "\n".join(parts), evidence_used


def _synthesize_event(evidence):
    """Synthesize answer for event queries."""
    events = evidence.get("events", [])
    
    if not events:
        return "No matching evidence was found.", []
    
    evidence_used = []
    parts = ["Matching events:"]
    
    for event in events:
        ts = event.get("timestamp", "Unknown")
        etype = event.get("event_type", "event")
        desc = event.get("description", "")
        parts.append(f"- {ts} [{etype}]: {desc}")
        evidence_used.append(f"event:{ts}")
    
    return "\n".join(parts), evidence_used


def _synthesize_document(evidence):
    """Synthesize answer for document queries."""
    documents = evidence.get("documents", [])
    
    if not documents:
        return "No matching evidence was found.", []
    
    evidence_used = []
    parts = [f"Found {len(documents)} matching document(s):"]
    
    for doc in documents:
        path = doc.get("path", "Unknown")
        parts.append(f"- {path}")
        evidence_used.append(f"doc:{path}")
    
    return "\n".join(parts), evidence_used


def _calculate_confidence(evidence, required_keys):
    """Calculate confidence score based on available evidence."""
    found_count = 0
    total_count = len(required_keys)
    
    for key in required_keys:
        if evidence.get(key):
            found_count += 1
    
    if found_count == 0:
        return 0.0
    elif found_count == total_count:
        return 1.0
    else:
        return 0.5