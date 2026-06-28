def build_dependency_graph(documents):
    graph = {}
    
    for doc in documents:
        path = doc.get('path', '')
        
        # Handle PythonParser structured_data format
        structured_data = doc.get('structured_data')
        if structured_data and isinstance(structured_data, dict):
            imports = structured_data.get('imports', [])
        else:
            imports = doc.get('imports', [])
        
        if path:
            graph[path] = list(imports) if imports else []
    
    return graph