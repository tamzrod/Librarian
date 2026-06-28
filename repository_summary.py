def summarize_repository(index):
    extensions = {}
    total_characters = 0
    total_chunks = 0
    files_with_structured_data = 0
    largest_file = None
    
    for doc in index:
        ext = doc.get('extension')
        if ext:
            extensions[ext] = extensions.get(ext, 0) + 1
        
        char_count = doc.get('character_count', 0)
        total_characters += char_count
        
        chunks = doc.get('chunks', [])
        total_chunks += len(chunks)
        
        if doc.get('has_structured_data'):
            files_with_structured_data += 1
        
        if largest_file is None or char_count > largest_file.get('character_count', 0):
            largest_file = {
                'path': doc.get('path'),
                'character_count': char_count
            }
    
    return {
        'total_files': len(index),
        'extensions': extensions,
        'total_characters': total_characters,
        'total_chunks': total_chunks,
        'files_with_structured_data': files_with_structured_data,
        'largest_file': largest_file
    }