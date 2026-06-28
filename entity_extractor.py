import re


def extract_entities(document):
    text = document.get('text', '')
    structured_data = document.get('structured_data')
    path = document.get('path', '')
    
    entities = []
    seen = set()
    
    # Email pattern
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    for match in email_pattern.finditer(text):
        entity_key = ('email', match.group())
        if entity_key not in seen:
            entities.append({
                'type': 'email',
                'value': match.group(),
                'source': path
            })
            seen.add(entity_key)
    
    # URL pattern
    url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
    for match in url_pattern.finditer(text):
        entity_key = ('url', match.group())
        if entity_key not in seen:
            entities.append({
                'type': 'url',
                'value': match.group(),
                'source': path
            })
            seen.add(entity_key)
    
    # Phone pattern (various formats)
    phone_pattern = re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b')
    for match in phone_pattern.finditer(text):
        value = re.sub(r'[^\d+]', '', match.group())
        entity_key = ('phone', value)
        if entity_key not in seen:
            entities.append({
                'type': 'phone',
                'value': value,
                'source': path
            })
            seen.add(entity_key)
    
    # Date patterns
    date_patterns = [
        re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'),
        re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'),
        re.compile(r'\b\d{4}-\d{2}-\d{2}\b'),
        re.compile(r'\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}'),
    ]
    for pattern in date_patterns:
        for match in pattern.finditer(text):
            entity_key = ('date', match.group())
            if entity_key not in seen:
                entities.append({
                    'type': 'date',
                    'value': match.group(),
                    'source': path
                })
                seen.add(entity_key)
    
    # Extract from structured_data if available
    if structured_data:
        if isinstance(structured_data, dict):
            for key, value in structured_data.items():
                if isinstance(value, str):
                    _extract_from_value(value, key, path, entities, seen)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            _extract_from_value(item, key, path, entities, seen)
                        elif isinstance(item, dict):
                            for v in item.values():
                                if isinstance(v, str):
                                    _extract_from_value(v, key, path, entities, seen)
        elif isinstance(structured_data, list):
            for item in structured_data:
                if isinstance(item, str):
                    _extract_from_value(item, 'list', path, entities, seen)
    
    return entities


def _extract_from_value(value, key, path, entities, seen):
    # Try to identify entity type based on key or value pattern
    key_lower = key.lower()
    value_lower = value.lower()
    
    # Person names heuristic (key contains name-related words)
    if any(word in key_lower for word in ['name', 'person', 'customer', 'client', 'user', 'owner']):
        entity_key = ('person', value)
        if entity_key not in seen:
            entities.append({
                'type': 'person',
                'value': value,
                'source': path
            })
            seen.add(entity_key)
    
    # Organization heuristic (key contains org-related words)
    if any(word in key_lower for word in ['company', 'organization', 'org', 'business', 'firm']):
        entity_key = ('organization', value)
        if entity_key not in seen:
            entities.append({
                'type': 'organization',
                'value': value,
                'source': path
            })
            seen.add(entity_key)
    
    # Location heuristic (key contains location-related words)
    if any(word in key_lower for word in ['location', 'address', 'city', 'country', 'region', 'place']):
        entity_key = ('location', value)
        if entity_key not in seen:
            entities.append({
                'type': 'location',
                'value': value,
                'source': path
            })
            seen.add(entity_key)