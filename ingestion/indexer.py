def index_document(document):
    text = document.get('text', '') or ''
    structured_data = document.get('structured_data')
    chunks = document.get('chunks', [])
    
    chunk_count = len(chunks)
    word_count = len(text.split())
    has_structured_data = structured_data is not None and structured_data != {}
    
    return {
        'path': document.get('path'),
        'extension': document.get('extension'),
        'text': text,
        'structured_data': structured_data,
        'character_count': document.get('character_count'),
        'chunks': chunks,
        'chunk_count': chunk_count,
        'word_count': word_count,
        'has_structured_data': has_structured_data,
        'sha256_hash': document.get('sha256_hash'),
        'modified_time': document.get('modified_time'),
        'file_size': document.get('file_size')
    }
