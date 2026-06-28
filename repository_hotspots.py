def find_hotspots(index, dependency_graph):
    IGNORE_PATTERNS = [
        'sample.',
        '_index.json',
        '.log',
        '.cache',
        '.tmp',
        '__pycache__/',
        '/.git/'
    ]
    
    def should_ignore(path):
        for pattern in IGNORE_PATTERNS:
            if pattern in path:
                return True
        return False
    
    # Calculate inbound dependencies
    inbound_counts = {}
    for path, imports in dependency_graph.items():
        for module in imports:
            module_clean = module.replace('/', '.').replace('\\', '.')
            if module_clean not in inbound_counts:
                inbound_counts[module_clean] = 0
            inbound_counts[module_clean] += 1
    
    hotspots = []
    
    for doc in index:
        path = doc.get('path')
        if not path or should_ignore(path):
            continue
        
        # Get filename without extension for matching
        filename = path.rsplit('/', 1)[-1] if '/' in path else path
        filename = filename.rsplit('\\', 1)[-1] if '\\' in filename else filename
        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        outbound_dependencies = len(dependency_graph.get(path, []))
        inbound_dependencies = inbound_counts.get(base_name, 0)
        
        word_count = doc.get('word_count', 0)
        chunk_count = doc.get('chunk_count', 0)
        
        score = inbound_dependencies * 20 + outbound_dependencies * 5 + chunk_count + word_count / 1000
        
        hotspots.append({
            'path': path,
            'score': score,
            'inbound_dependencies': inbound_dependencies,
            'outbound_dependencies': outbound_dependencies,
            'word_count': word_count,
            'chunk_count': chunk_count
        })
    
    hotspots.sort(key=lambda x: (x['score'], x['inbound_dependencies'], x['outbound_dependencies']), reverse=True)
    
    return hotspots