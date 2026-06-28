from retriever import search_documents
from entity_extractor import extract_entities


def build_evidence_package(index, query):
    documents = search_documents(index, query)
    
    all_entities = []
    all_sources = []
    all_timestamps = []
    all_locations = []
    
    seen_entities = set()
    seen_sources = set()
    seen_timestamps = set()
    seen_locations = set()
    
    for doc in documents:
        path = doc.get('path', '')
        if path and path not in seen_sources:
            all_sources.append(path)
            seen_sources.add(path)
        
        timestamp = doc.get('modified_time')
        if timestamp and timestamp not in seen_timestamps:
            all_timestamps.append(timestamp)
            seen_timestamps.add(timestamp)
        
        entities = extract_entities(doc)
        for entity in entities:
            entity_key = (entity['type'], entity['value'])
            if entity_key not in seen_entities:
                all_entities.append(entity)
                seen_entities.add(entity_key)
            
            if entity['type'] == 'location' and entity['value'] not in seen_locations:
                all_locations.append(entity['value'])
                seen_locations.add(entity['value'])
    
    return {
        "query": query,
        "documents": documents,
        "entities": all_entities,
        "sources": all_sources,
        "timestamps": sorted(all_timestamps),
        "locations": all_locations
    }