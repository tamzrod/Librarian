"""
Test PostgreSQL indexes with EXPLAIN ANALYZE.
This requires a running PostgreSQL instance.
"""
import os
import subprocess
import time


def run_sql(sql, params=None):
    """Execute SQL and return result."""
    cmd = [
        'psql',
        '-h', os.environ.get('PGHOST', 'localhost'),
        '-p', os.environ.get('PGPORT', '5432'),
        '-U', os.environ.get('PGUSER', 'librarian'),
        '-d', os.environ.get('PGDATABASE', 'librarian'),
        '-c', sql
    ]
    env = os.environ.copy()
    env['PGPASSWORD'] = os.environ.get('PGPASSWORD', 'librarian')
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.stdout + result.stderr


def setup_database():
    """Initialize empty database and run migrations."""
    print("=" * 70)
    print("STEP 1: Setting up database")
    print("=" * 70)
    
    # Create database if not exists
    create_db = """
    SELECT 'CREATE DATABASE librarian'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'librarian');
    """
    
    # Drop and recreate tables
    drop_sql = """
    DROP TABLE IF EXISTS document_locations CASCADE;
    DROP TABLE IF EXISTS document_events CASCADE;
    DROP TABLE IF EXISTS document_entities CASCADE;
    DROP TABLE IF EXISTS relationships CASCADE;
    DROP TABLE IF EXISTS locations CASCADE;
    DROP TABLE IF EXISTS events CASCADE;
    DROP TABLE IF EXISTS entities CASCADE;
    DROP TABLE IF EXISTS documents CASCADE;
    DROP TABLE IF EXISTS collections CASCADE;
    """
    run_sql(drop_sql)
    
    # Run migrations
    schema_path = 'storage/migrations/schema.sql'
    with open(schema_path, 'r') as f:
        schema = f.read()
    
    # Execute schema
    for statement in schema.split(';'):
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            run_sql(statement)
    
    print("Database initialized with schema and indexes.")
    
    # Insert sample data
    print("\nInserting sample data...")
    
    # Insert documents
    run_sql("""
    INSERT INTO documents (path, extension, modified_time) VALUES
    ('/path/to/doc1.pdf', 'pdf', '2026-01-01 10:00:00'),
    ('/path/to/doc2.pdf', 'pdf', '2026-01-15 10:00:00'),
    ('/path/to/doc3.jpg', 'jpg', '2026-01-15 11:00:00'),
    ('/path/to/doc4.pdf', 'pdf', '2026-02-01 10:00:00');
    """)
    
    # Insert entities
    run_sql("""
    INSERT INTO entities (type, value) VALUES
    ('organization', 'ABC Corp'),
    ('person', 'John Smith'),
    ('device', 'HONOR BRP-NX1');
    """)
    
    # Insert events
    run_sql("""
    INSERT INTO events (timestamp, event_type, description) VALUES
    ('2026-01-01', 'photo', 'Photo taken'),
    ('2026-01-15', 'site_visit', 'Site visit at Marikina'),
    ('2026-02-01', 'maintenance', 'Maintenance visit');
    """)
    
    # Insert locations
    run_sql("""
    INSERT INTO locations (name, latitude, longitude) VALUES
    ('Manila', 14.5995, 120.9842),
    ('Marikina', 14.6389, 121.1156),
    ('Makati', 14.5547, 121.0244);
    """)
    
    # Insert relationships
    run_sql("""
    INSERT INTO relationships (from_entity, to_entity, relationship_type) VALUES
    ('ABC Corp', 'Manila', 'located_in'),
    ('John Smith', 'ABC Corp', 'works_for');
    """)
    
    # Link documents to entities
    run_sql("""
    INSERT INTO document_entities (document_id, entity_id) VALUES
    (1, 1), (2, 1), (4, 1),
    (2, 2),
    (3, 3);
    """)
    
    # Link documents to events
    run_sql("""
    INSERT INTO document_events (document_id, event_id) VALUES
    (3, 1), (2, 2), (4, 3);
    """)
    
    # Link documents to locations
    run_sql("""
    INSERT INTO document_locations (document_id, location_id) VALUES
    (3, 1), (2, 2), (1, 1);
    """)
    
    print("Sample data inserted.")


def explain_query(name, sql):
    """Run EXPLAIN ANALYZE for a query."""
    print("\n" + "=" * 70)
    print(f"QUERY: {name}")
    print("=" * 70)
    
    explain_sql = f"EXPLAIN ANALYZE {sql}"
    result = run_sql(explain_sql)
    
    # Extract relevant parts
    lines = result.split('\n')
    for line in lines:
        if 'Index' in line or 'Scan' in line or 'Cost' in line or 'Execution' in line:
            print(line)


def main():
    print("PostgreSQL Index Verification Test")
    print("=" * 70)
    
    # Check if PostgreSQL is available
    try:
        result = run_sql("SELECT version();")
        if 'PostgreSQL' not in result:
            print("ERROR: PostgreSQL not available")
            print("Set environment variables: PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD")
            return
        print("Connected to PostgreSQL:")
        print(result.split('\n')[0])
    except Exception as e:
        print(f"ERROR: Could not connect to PostgreSQL: {e}")
        print("Make sure PostgreSQL is running and environment variables are set.")
        return
    
    # Setup
    setup_database()
    
    # Explain ANALYZE for key queries
    print("\n" + "=" * 70)
    print("STEP 2: Analyzing query plans with indexes")
    print("=" * 70)
    
    # search_events(date)
    explain_query(
        "search_events(date='2026-01-01')",
        """
        SELECT e.id, e.timestamp, e.event_type, e.description
        FROM events e
        WHERE e.timestamp >= '2026-01-01'
          AND e.timestamp < '2026-01-02'
        """
    )
    
    # search_entities(value)
    explain_query(
        "search_entities(value='ABC Corp')",
        """
        SELECT e.id, e.type, e.value
        FROM entities e
        WHERE e.value ILIKE '%ABC Corp%'
        """
    )
    
    # search_documents(entity)
    explain_query(
        "search_documents(entity='ABC Corp')",
        """
        SELECT d.id, d.path
        FROM documents d
        WHERE EXISTS (
            SELECT 1 FROM document_entities de
            JOIN entities e ON de.entity_id = e.id
            WHERE de.document_id = d.id AND e.value ILIKE '%ABC Corp%'
        )
        """
    )
    
    # search_relationships(entity)
    explain_query(
        "search_relationships(entity='ABC Corp')",
        """
        SELECT id, from_entity, to_entity, relationship_type
        FROM relationships
        WHERE from_entity ILIKE '%ABC Corp%' OR to_entity ILIKE '%ABC Corp%'
        """
    )
    
    # List all indexes
    print("\n" + "=" * 70)
    print("STEP 3: All indexes created")
    print("=" * 70)
    result = run_sql("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE schemaname = 'public' 
        ORDER BY indexname;
    """)
    print(result)


if __name__ == "__main__":
    main()