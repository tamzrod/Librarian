import re
from datetime import datetime


def extract_events(document):
    events = []
    seen = set()
    
    text = document.get('text', '')
    structured_data = document.get('structured_data')
    entities = document.get('entities', [])
    modified_time = document.get('modified_time')
    path = document.get('path', '')
    
    # Extract events from date entities
    for entity in entities:
        if entity.get('type') == 'date':
            timestamp = entity.get('value', '')
            if timestamp and timestamp not in seen:
                events.append({
                    'timestamp': timestamp,
                    'event_type': 'document_date',
                    'description': f"Date mentioned in document: {timestamp}",
                    'source': path
                })
                seen.add(timestamp)
    
    # Extract events from file modified timestamp
    if modified_time:
        mod_time_str = str(modified_time)
        if mod_time_str not in seen:
            events.append({
                'timestamp': mod_time_str,
                'event_type': 'file_modified',
                'description': f"File last modified: {path}",
                'source': path
            })
            seen.add(mod_time_str)
    
    # Extract events from structured_data timestamps
    if structured_data:
        _extract_from_structured_data(structured_data, path, events, seen)
    
    return events


def _extract_from_structured_data(data, source, events, seen):
    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = key.lower()
            if any(word in key_lower for word in ['date', 'time', 'timestamp', 'created', 'modified', 'updated']):
                if isinstance(value, str) and value:
                    if _is_likely_timestamp(value):
                        if value not in seen:
                            events.append({
                                'timestamp': value,
                                'event_type': f'structured_data_{key_lower}',
                                'description': f"{key}: {value}",
                                'source': source
                            })
                            seen.add(value)
            elif isinstance(value, (dict, list)):
                _extract_from_structured_data(value, source, events, seen)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                _extract_from_structured_data(item, source, events, seen)


def _is_likely_timestamp(value):
    patterns = [
        r'\d{4}-\d{2}-\d{2}',
        r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}',
        r'\d{1,2}/\d{1,2}/\d{2,4}',
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
    ]
    for pattern in patterns:
        if re.search(pattern, value):
            return True
    return False