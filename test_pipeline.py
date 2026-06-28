import os
from scanner import parse_file
from chunker import chunk_text
from indexer import index_document
from persistence import save_index, load_index
from retriever import search_documents


def test_pipeline():
    sample_files = [f for f in os.listdir('.') if f.startswith('sample.') and os.path.isfile(f)]
    
    # 1. Scan sample files
    scanned_files = len(sample_files)
    
    # 2. Parse files and 3. Chunk parsed text
    indexed_docs = []
    for filename in sample_files:
        result = parse_file(filename)
        if result:
            chunks = chunk_text(result.get('text', ''))
            result['chunks'] = chunks
            # 4. Index documents
            indexed_doc = index_document(result)
            indexed_docs.append(indexed_doc)
    
    parsed_files = len(indexed_docs)
    indexed_files = len(indexed_docs)
    
    # 5. Save index
    save_index(indexed_docs, 'test_index.json')
    
    # 6. Reload index
    reloaded_index = load_index('test_index.json')
    
    # 7. Search for json, xml, yaml
    json_results = search_documents(reloaded_index, 'json')
    xml_results = search_documents(reloaded_index, 'xml')
    yaml_results = search_documents(reloaded_index, 'yaml')
    
    print(f"Number of scanned files: {scanned_files}")
    print(f"Number of parsed files: {parsed_files}")
    print(f"Number of indexed files: {indexed_files}")
    print(f"Results for 'json': {len(json_results)}")
    print(f"Results for 'xml': {len(xml_results)}")
    print(f"Results for 'yaml': {len(yaml_results)}")


if __name__ == "__main__":
    test_pipeline()
