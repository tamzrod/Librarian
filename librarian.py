import os
from scanner import parse_file
from chunker import chunk_text
from indexer import index_document
from retriever import search_documents
from dependency_indexer import extract_dependencies
from persistence import save_index, load_index


class Librarian:
    def __init__(self):
        self.index = []

    def ingest(self, path, persist_path=None):
        self.index = []
        
        for root, dirs, files in os.walk(path):
            if any(exclude in root for exclude in ['.git', '__pycache__', '.venv', 'node_modules']):
                continue
            
            for filename in files:
                full_path = os.path.join(root, filename)
                result = parse_file(full_path)
                if result:
                    result['path'] = full_path
                    chunks = chunk_text(result.get('text', ''))
                    result['chunks'] = chunks
                    indexed_doc = index_document(result)
                    self.index.append(indexed_doc)
        
        if persist_path:
            save_index(self.index, persist_path)

    def load_index(self, filename):
        self.index = load_index(filename)

    def search(self, query):
        return search_documents(self.index, query)

    def get_dependencies(self, file_path):
        with open(file_path, 'r') as f:
            text = f.read()
        return extract_dependencies(file_path, text)
