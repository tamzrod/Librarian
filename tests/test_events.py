import sys
sys.path.insert(0, '.')

from storage.postgres_backend import PostgresBackend


def main():
    backend = PostgresBackend(host='localhost', port=5432, dbname='librarian',
                               user='librarian', password='librarian')
    
    backend._ensure_schema()
    
    collection_id = backend.save_collection({
        'name': 'Test Collection',
        'root_path': '/tmp/test',
        'created_at': None
    })
    
    doc_id = backend.save_document({
        'collection_id': collection_id,
        'path': '/tmp/test/document.txt',
        'extension': '.txt',
        'sha256': 'abc123',
        'modified_time': None,
        'file_size': 1024,
        'character_count': 100,
        'parser': 'text',
        'indexed_at': None
    })
    
    events = [
        {
            'timestamp': '2025-03-12',
            'event_type': 'meeting',
            'description': 'Meeting scheduled for March 12, 2025'
        },
        {
            'timestamp': '2025-03-15',
            'event_type': 'deadline',
            'description': 'Project deadline March 15, 2025'
        },
        {
            'timestamp': '2025-04-01',
            'event_type': 'release',
            'description': 'Release scheduled for April 1, 2025'
        }
    ]
    
    backend.save_events(doc_id, events)
    
    conn = backend._get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM events")
    events_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM document_events")
    document_events_count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    print(f"events:\n{events_count}")
    print(f"document_events:\n{document_events_count}")


if __name__ == '__main__':
    main()