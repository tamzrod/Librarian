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
    
    locations = [
        {
            'name': 'Makati',
            'latitude': 14.5547,
            'longitude': 121.0244
        },
        {
            'name': 'Manila',
            'latitude': 14.5995,
            'longitude': 120.9842
        },
        {
            'name': 'Quezon City',
            'latitude': 14.6760,
            'longitude': 121.0437
        }
    ]
    
    backend.save_locations(doc_id, locations)
    
    conn = backend._get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM locations")
    locations_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM document_locations")
    document_locations_count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    print(f"locations:\n{locations_count}")
    print(f"document_locations:\n{document_locations_count}")


if __name__ == '__main__':
    main()