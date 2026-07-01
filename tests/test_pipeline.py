import os
from ingestion.scanner import parse_file
from ingestion.chunker import chunk_text
from ingestion.indexer import index_document
from ingestion.retriever import search_documents


SAMPLE_DIR = "samples/structured"


def test_pipeline():
    sample_files = [os.path.join(SAMPLE_DIR, f) for f in os.listdir(SAMPLE_DIR) if f.startswith('sample.') and os.path.isfile(os.path.join(SAMPLE_DIR, f))]
    
    # 1. Scan sample files
    scanned_files = len(sample_files)
    
    # 2. Parse files and 3. Chunk parsed text
    indexed_docs = []
    for filepath in sample_files:
        result = parse_file(filepath)
        if result:
            chunks = chunk_text(result.get('text', ''))
            result['chunks'] = chunks
            # 4. Index documents
            indexed_doc = index_document(result)
            indexed_docs.append(indexed_doc)
    
    parsed_files = len(indexed_docs)
    indexed_files = len(indexed_docs)
    
    # 5. Search in-memory (JSON persistence is deprecated; search directly)
    json_results = search_documents(indexed_docs, 'json')
    xml_results = search_documents(indexed_docs, 'xml')
    yaml_results = search_documents(indexed_docs, 'yaml')
    
    print(f"Number of scanned files: {scanned_files}")
    print(f"Number of parsed files: {parsed_files}")
    print(f"Number of indexed files: {indexed_files}")
    print(f"Results for 'json': {len(json_results)}")
    print(f"Results for 'xml': {len(xml_results)}")
    print(f"Results for 'yaml': {len(yaml_results)}")


if __name__ == "__main__":
    test_pipeline()
