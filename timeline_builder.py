from event_extractor import extract_events
from location_extractor import extract_locations


def build_timeline(index):
    timeline = []
    
    for doc in index:
        path = doc.get('path', '')
        structured_data = doc.get('structured_data', {})
        modified_time = doc.get('modified_time')
        
        timestamp = None
        event_type = None
        location = None
        
        # Check for EXIF timestamp in structured_data
        if structured_data:
            timestamp = structured_data.get('timestamp')
            if not timestamp and modified_time:
                timestamp = str(modified_time)
                event_type = 'file_modified'
        elif modified_time:
            timestamp = str(modified_time)
            event_type = 'file_modified'
        
        # Skip documents without timestamps
        if not timestamp:
            continue
        
        # Extract location if available
        entities = doc.get('entities', [])
        doc_with_entities = doc.copy()
        doc_with_entities['entities'] = entities
        
        locations = extract_locations(doc_with_entities)
        if locations:
            location = locations[0].get('name')
        
        # Get event type from extracted events
        events = extract_events(doc_with_entities)
        if events and not event_type:
            event_type = events[0].get('event_type', 'document')
        
        timeline.append({
            'timestamp': timestamp,
            'event_type': event_type or 'document',
            'location': location,
            'source': path
        })
    
    # Sort by timestamp ascending
    timeline.sort(key=lambda x: x['timestamp'])
    
    return timeline