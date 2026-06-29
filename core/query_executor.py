def execute_query(plan, backend):
    """
    Execute a query plan against the storage backend and build an evidence package.
    
    Args:
        plan: Dict with intent, required_evidence, and filters
        backend: StorageBackend instance
    
    Returns:
        Dict with intent and evidence package
    """
    evidence = {
        "documents": [],
        "entities": [],
        "events": [],
        "locations": [],
        "relationships": []
    }
    
    intent = plan.get("intent", "unknown")
    required = plan.get("required_evidence", [])
    filters = plan.get("filters", {})
    
    # Execute based on intent and required evidence types
    if intent == "location_query":
        evidence = _execute_location_query(plan, backend, filters)
    elif intent == "timeline_query":
        evidence = _execute_timeline_query(plan, backend, filters)
    elif intent == "entity_query":
        evidence = _execute_entity_query(plan, backend, filters)
    elif intent == "profile_query":
        evidence = _execute_profile_query(plan, backend, filters)
    elif intent == "event_query":
        evidence = _execute_event_query(plan, backend, filters)
    elif intent == "document_query":
        evidence = _execute_document_query(plan, backend, filters)
    else:
        # Fallback to generic execution
        evidence = _execute_generic(plan, backend, filters)
    
    return {
        "intent": intent,
        "evidence": evidence
    }


def _execute_location_query(plan, backend, filters):
    """Execute location query with date filtering."""
    evidence = {"documents": [], "entities": [], "events": [], "locations": [], "relationships": []}
    date_filter = filters.get("date", "")
    
    # Search events with date filter
    events = _search_events(backend, date_filter, None)
    if date_filter:
        events = _filter_events_by_date(events, date_filter)
    evidence["events"] = events
    
    # Search locations - filter by date if location has date association
    locations = _search_locations(backend, None)
    if date_filter:
        locations = _filter_locations_by_date(locations, date_filter)
    evidence["locations"] = locations
    
    # Search documents with date filter
    documents = _search_documents(backend, date_filter)
    if date_filter:
        documents = _filter_documents_by_date(documents, date_filter)
    evidence["documents"] = documents
    
    return evidence


def _execute_timeline_query(plan, backend, filters):
    """Execute timeline query with month filtering."""
    evidence = {"documents": [], "entities": [], "events": [], "locations": [], "relationships": []}
    month_filter = filters.get("month", "")
    
    # Search events with month filter
    events = _search_events(backend, None, None)
    if month_filter:
        events = _filter_events_by_month(events, month_filter)
    evidence["events"] = events
    
    # Search documents with month filter
    documents = _search_documents(backend, None)
    if month_filter:
        documents = _filter_documents_by_month(documents, month_filter)
    evidence["documents"] = documents
    
    return evidence


def _execute_entity_query(plan, backend, filters):
    """Execute entity query with entity filtering."""
    evidence = {"documents": [], "entities": [], "events": [], "locations": [], "relationships": []}
    entity_filter = filters.get("entity", "")
    
    # Search entities by value
    entities = _search_entities(backend, None, entity_filter)
    evidence["entities"] = entities
    
    # Search documents containing the entity
    documents = _search_documents(backend, entity_filter)
    evidence["documents"] = documents
    
    # Search events related to the entity
    events = _search_events(backend, None, None)
    if entity_filter:
        events = _filter_events_by_entity(events, entity_filter)
    evidence["events"] = events
    
    return evidence


def _execute_profile_query(plan, backend, filters):
    """Execute profile query with entity filtering."""
    evidence = {"documents": [], "entities": [], "events": [], "locations": [], "relationships": []}
    entity_filter = filters.get("entity", "")
    
    # Search entities by value
    entities = _search_entities(backend, None, entity_filter)
    evidence["entities"] = entities
    
    # Search relationships involving the entity
    relationships = _search_relationships(backend, filters)
    if entity_filter:
        relationships = _filter_relationships_by_entity(relationships, entity_filter)
    evidence["relationships"] = relationships
    
    # Search events related to the entity
    events = _search_events(backend, None, None)
    if entity_filter:
        events = _filter_events_by_entity(events, entity_filter)
    evidence["events"] = events
    
    # Search documents containing the entity
    documents = _search_documents(backend, entity_filter)
    evidence["documents"] = documents
    
    return evidence


def _execute_event_query(plan, backend, filters):
    """Execute event query."""
    evidence = {"documents": [], "entities": [], "events": [], "locations": [], "relationships": []}
    events = _search_events(backend, None, None)
    evidence["events"] = events
    return evidence


def _execute_document_query(plan, backend, filters):
    """Execute document query."""
    evidence = {"documents": [], "entities": [], "events": [], "locations": [], "relationships": []}
    query = filters.get("query", "")
    documents = _search_documents(backend, query)
    evidence["documents"] = documents
    return evidence


def _execute_generic(plan, backend, filters):
    """Generic fallback execution."""
    evidence = {"documents": [], "entities": [], "events": [], "locations": [], "relationships": []}
    required = plan.get("required_evidence", [])
    
    if "documents" in required:
        evidence["documents"] = _search_documents(backend, filters.get("query", ""))
    if "entities" in required:
        evidence["entities"] = _search_entities(backend, None, filters.get("entity"))
    if "events" in required:
        evidence["events"] = _search_events(backend, filters.get("date"), None)
    if "locations" in required:
        evidence["locations"] = _search_locations(backend, filters.get("location"))
    if "relationships" in required:
        evidence["relationships"] = _search_relationships(backend, filters)
    
    return evidence


def _search_documents(backend, query):
    """Search for documents matching the query."""
    if hasattr(backend, 'search_documents'):
        try:
            return backend.search_documents(query or "") or []
        except Exception:
            return []
    return []


def _search_entities(backend, entity_type, value):
    """Search for entities matching the type and value."""
    if hasattr(backend, 'search_entities'):
        try:
            return backend.search_entities(entity_type, value) or []
        except Exception:
            return []
    return []


def _search_events(backend, timestamp, event_type):
    """Search for events matching the timestamp and type."""
    if hasattr(backend, 'search_events'):
        try:
            return backend.search_events(timestamp, event_type) or []
        except Exception:
            return []
    return []


def _search_locations(backend, location_name):
    """Search for locations matching the name."""
    if hasattr(backend, 'search_locations'):
        try:
            return backend.search_locations(location_name) or []
        except Exception:
            return []
    return []


def _search_relationships(backend, filters):
    """Search for relationships."""
    if hasattr(backend, 'search_relationships'):
        try:
            return backend.search_relationships(filters) or []
        except Exception:
            return []
    return []


def _filter_events_by_date(events, date_filter):
    """Filter events by date string."""
    filtered = []
    for event in events:
        ts = event.get("timestamp", "")
        # Handle various date formats in the filter
        if date_filter.lower() in ts.lower():
            filtered.append(event)
        # Handle "January 1 2026" format
        elif _date_matches(date_filter, ts):
            filtered.append(event)
    return filtered


def _filter_events_by_month(events, month_filter):
    """Filter events by month (YYYY-MM format)."""
    filtered = []
    for event in events:
        ts = event.get("timestamp", "")
        if ts.startswith(month_filter):
            filtered.append(event)
    return filtered


def _filter_events_by_entity(events, entity_filter):
    """Filter events related to an entity."""
    filtered = []
    for event in events:
        desc = event.get("description", "").lower()
        if entity_filter.lower() in desc:
            filtered.append(event)
    return filtered


def _filter_locations_by_date(locations, date_filter):
    """Filter locations by date association."""
    filtered = []
    for location in locations:
        source = location.get("source", "")
        ts = location.get("timestamp", "")
        if date_filter.lower() in source.lower() or _date_matches(date_filter, ts):
            filtered.append(location)
    return filtered


def _filter_documents_by_date(documents, date_filter):
    """Filter documents by date."""
    filtered = []
    for doc in documents:
        path = doc.get("path", "").lower()
        text = str(doc.get("text", "")).lower()
        if date_filter.lower() in path or date_filter.lower() in text:
            filtered.append(doc)
    return filtered


def _filter_documents_by_month(documents, month_filter):
    """Filter documents by month."""
    filtered = []
    for doc in documents:
        path = doc.get("path", "").lower()
        text = str(doc.get("text", "")).lower()
        if month_filter in path or month_filter in text:
            filtered.append(doc)
    return filtered


def _filter_relationships_by_entity(relationships, entity_filter):
    """Filter relationships involving an entity."""
    filtered = []
    for rel in relationships:
        from_ent = rel.get("from", "").lower()
        to_ent = rel.get("to", "").lower()
        if entity_filter.lower() in from_ent or entity_filter.lower() in to_ent:
            filtered.append(rel)
    return filtered


def _date_matches(filter_text, timestamp):
    """Check if a date filter matches a timestamp."""
    # Handle "January 1 2026" -> "2026-01-01"
    import re
    month_map = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12'
    }
    
    # Try to parse "January 1 2026" or "Jan 1, 2026"
    pattern = r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})'
    match = re.match(pattern, filter_text)
    if match:
        month_str, day, year = match.groups()
        month_str = month_str.lower()
        if month_str in month_map:
            filter_date = f"{year}-{month_map[month_str]}-{day.zfill(2)}"
            return filter_date in timestamp
    return False