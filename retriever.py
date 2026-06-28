def search_documents(index, query):
    if not query:
        return []
    
    query_lower = query.lower()
    matches = []
    
    for doc in index:
        text = doc.get('text', '') or ''
        structured_data = doc.get('structured_data')
        extension = doc.get('extension', '') or ''
        
        structured_str = ''
        if structured_data:
            structured_str = str(structured_data)
        
        if (query_lower in text.lower() or 
            query_lower in structured_str.lower() or 
            query_lower in extension.lower()):
            matches.append(doc)
    
    return matches
