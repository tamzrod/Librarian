import os
import hashlib
from indexing.scanner import parse_file
from indexing.chunker import chunk_text
from indexing.indexer import index_document
from indexing.retriever import search_documents
from graph.dependency_indexer import extract_dependencies
from indexing.persistence import save_index, load_index


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
                    with open(full_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    result['path'] = full_path
                    result['sha256_hash'] = file_hash
                    result['modified_time'] = os.path.getmtime(full_path)
                    result['file_size'] = os.path.getsize(full_path)
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

    def detect_changes(self, previous_index_path, current_index=None):
        if current_index is None:
            current_index = self.index
        
        previous_index = load_index(previous_index_path)
        
        prev_dict = {doc['path']: doc for doc in previous_index if 'path' in doc}
        curr_dict = {doc['path']: doc for doc in current_index if 'path' in doc}
        
        added = []
        removed = []
        modified = []
        unchanged = []
        
        for path, prev_doc in prev_dict.items():
            if path not in curr_dict:
                removed.append(prev_doc)
            else:
                curr_doc = curr_dict[path]
                prev_count = prev_doc.get('character_count')
                curr_count = curr_doc.get('character_count')
                prev_words = prev_doc.get('word_count')
                curr_words = curr_doc.get('word_count')
                
                if prev_count != curr_count or prev_words != curr_words:
                    modified.append(curr_doc)
                else:
                    unchanged.append(curr_doc)
        
        for path, curr_doc in curr_dict.items():
            if path not in prev_dict:
                added.append(curr_doc)
        
        return {
            "added": added,
            "removed": removed,
            "modified": modified,
            "unchanged": unchanged
        }
