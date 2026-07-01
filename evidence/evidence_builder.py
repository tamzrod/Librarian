class EvidenceBuilder:
    def __init__(self, backend):
        self.backend = backend

    def get_documents(self, query):
        return self.backend.search_documents(query) or []

    def get_entities(self, entity_type=None, value=None):
        return self.backend.search_entities(entity_type, value) or []

    def get_events(self, timestamp=None, event_type=None):
        return self.backend.search_events(timestamp, event_type) or []

    def get_locations(self, location_name=None):
        return self.backend.search_locations(location_name) or []


def build_evidence(question, planner_result, backend):
    evidence = {
        "documents": [],
        "entities": [],
        "events": [],
        "locations": []
    }
    
    builder = EvidenceBuilder(backend)
    
    request_type = planner_result.get('type', '')
    
    if request_type == 'documents' or 'document' in request_type.lower():
        query = planner_result.get('query', question)
        evidence["documents"] = builder.get_documents(query)
    
    if request_type == 'entities' or 'entity' in request_type.lower():
        entity_type = planner_result.get('entity_type')
        value = planner_result.get('value')
        evidence["entities"] = builder.get_entities(entity_type, value)
    
    if request_type == 'events' or 'event' in request_type.lower():
        timestamp = planner_result.get('timestamp')
        event_type = planner_result.get('event_type')
        evidence["events"] = builder.get_events(timestamp, event_type)
    
    if request_type == 'locations' or 'location' in request_type.lower():
        location_name = planner_result.get('location_name')
        evidence["locations"] = builder.get_locations(location_name)
    
    # Check for explicit flags
    if planner_result.get('retrieve_documents'):
        query = planner_result.get('query', question)
        evidence["documents"] = builder.get_documents(query)
    
    if planner_result.get('retrieve_entities'):
        evidence["entities"] = builder.get_entities()
    
    if planner_result.get('retrieve_events'):
        evidence["events"] = builder.get_events()
    
    if planner_result.get('retrieve_locations'):
        evidence["locations"] = builder.get_locations()
    
    return {
        "question": question,
        "intent": planner_result.get('intent', 'unknown'),
        "evidence": evidence
    }