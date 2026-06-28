def chunk_text(text, max_size=1000):
    if not text:
        return []
    
    chunks = []
    for i in range(0, len(text), max_size):
        chunks.append(text[i:i + max_size])
    
    return chunks
