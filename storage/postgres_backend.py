import os
import logging
import psycopg
from .backend import StorageBackend

logger = logging.getLogger(__name__)


class PostgresBackend(StorageBackend):
    def __init__(self, host='localhost', port=5432, dbname='librarian',
                 user='librarian', password='librarian'):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self._connection = None
        self._schema_verified = False

    def _get_connection(self):
        return psycopg.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password
        )

    def _check_tables_exist(self) -> bool:
        """Check if core tables exist in the database."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'documents'
                )
            """)
            exists = cur.fetchone()[0]
            cur.close()
            conn.close()
            return exists
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            return False
    
    def _ensure_migrations_table(self) -> bool:
        """Ensure the schema_migrations tracking table exists."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    migration_name VARCHAR(255) NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error creating migrations table: {e}")
            return False
    
    def _get_applied_migrations(self) -> set:
        """Get set of already applied migration names."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT migration_name FROM schema_migrations")
            migrations = {row[0] for row in cur.fetchall()}
            cur.close()
            conn.close()
            return migrations
        except Exception as e:
            logger.warning(f"Could not get applied migrations: {e}")
            return set()
    
    def _record_migration(self, migration_name: str) -> bool:
        """Record that a migration has been applied."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO schema_migrations (migration_name) VALUES (%s) ON CONFLICT DO NOTHING",
                (migration_name,)
            )
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error recording migration: {e}")
            return False

    def _get_schema_path(self) -> str:
        """Get the path to the schema.sql file."""
        # Try multiple locations for the schema file
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'migrations', 'schema.sql'),
            '/app/storage/migrations/schema.sql',
            os.path.join(os.getcwd(), 'storage', 'migrations', 'schema.sql'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return possible_paths[0]  # Return first option for error message

    def _check_unique_constraint_exists(self) -> bool:
        """Check if the unique constraint on documents.path exists."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_type = 'UNIQUE'
                AND table_name = 'documents'
                AND constraint_name LIKE '%path%'
            """)
            exists = cur.fetchone() is not None
            cur.close()
            conn.close()
            return exists
        except Exception as e:
            logger.debug(f"Error checking unique constraint: {e}")
            return False
    
    def _run_schema_migrations(self) -> bool:
        """Run additional schema migrations for existing databases."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Migration 002: Add unique index on documents.path for UPSERT support
            # This handles existing databases that don't have the UNIQUE constraint
            if '002_documents_path_unique' not in self._get_applied_migrations():
                if not self._check_unique_constraint_exists():
                    logger.info("Running migration: adding unique index on documents.path")
                    cur.execute("""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_path_unique 
                        ON documents(path)
                    """)
                    conn.commit()
                self._record_migration('002_documents_path_unique')
                logger.info("Migration 002 completed: documents.path unique index added")
            
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error running schema migrations: {e}")
            return False

    def ensure_schema(self) -> bool:
        """
        Ensure database schema exists, creating it if necessary.
        
        Uses migration tracking to prevent duplicate execution and
        support future schema upgrades.
        
        Returns:
            True if schema is ready, False on failure
        """
        if self._schema_verified:
            return True
        
        try:
            # First, ensure migrations table exists
            self._ensure_migrations_table()
            
            # Check for existing initial migration
            applied = self._get_applied_migrations()
            
            # Check if tables already exist
            if self._check_tables_exist():
                # Tables exist - run any pending migrations
                self._run_schema_migrations()
                
                # Check if we have migration record
                if '001_initial' not in applied:
                    # Tables exist but no migration record - record it
                    self._record_migration('001_initial')
                logger.info("Database schema already exists")
                self._schema_verified = True
                return True
            
            # Schema doesn't exist, create it
            logger.warning("Database schema not found, creating...")
            
            schema_path = self._get_schema_path()
            if not os.path.exists(schema_path):
                logger.error(f"Schema file not found at: {schema_path}")
                return False
            
            # Read and execute schema
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Execute each statement separately
            statements = []
            current_stmt = []
            for line in schema_sql.split('\n'):
                stripped = line.strip()
                # Skip comments and empty lines
                if not stripped or stripped.startswith('--'):
                    continue
                current_stmt.append(line)
                if stripped.endswith(';'):
                    statements.append('\n'.join(current_stmt))
                    current_stmt = []
            
            # Execute each statement
            for stmt in statements:
                stmt = stmt.strip()
                if stmt:
                    try:
                        cur.execute(stmt)
                    except Exception as e:
                        # Log but continue - some statements might fail on re-run
                        logger.debug(f"Statement execution note: {e}")
            
            conn.commit()
            cur.close()
            conn.close()
            
            # Run any additional migrations after initial schema creation
            self._run_schema_migrations()
            
            # Verify schema was created
            if self._check_tables_exist():
                logger.info("Database schema created successfully")
                # Record the migration
                self._record_migration('001_initial')
                self._schema_verified = True
                return True
            else:
                logger.error("Schema creation failed - tables still don't exist")
                return False
                
        except Exception as e:
            logger.error(f"Error ensuring schema: {e}")
            return False

    def save_document(self, document):
        """Save a document to the database.
        
        Canonical schema columns: path, extension, sha256, file_size, 
        character_count, parser, modified_time, indexed_at
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        path = document.get('path', '')
        
        # Map legacy input keys to canonical schema columns
        # hash → sha256, size_bytes → file_size
        sha256 = document.get('sha256') or document.get('hash')
        file_size = document.get('file_size') or document.get('size_bytes')
        character_count = document.get('character_count')
        modified_time = document.get('modified_time')
        parser = document.get('parser')
        extension = document.get('extension')
        
        cur.execute(
            """
            INSERT INTO documents (path, extension, sha256, file_size, character_count, parser, modified_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (path) DO UPDATE SET
                extension = EXCLUDED.extension,
                sha256 = EXCLUDED.sha256,
                file_size = EXCLUDED.file_size,
                character_count = EXCLUDED.character_count,
                parser = EXCLUDED.parser,
                modified_time = EXCLUDED.modified_time
            RETURNING id
            """,
            (path, extension, sha256, file_size, character_count, parser, modified_time)
        )
        document_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return document_id

    def save_entities(self, document_id, entities):
        """Save entities to the database.
        
        Canonical schema columns: value, type, normalized_value
        Supports legacy 'name' key mapped to 'value'.
        """
        conn = self._get_connection()
        cur = conn.cursor()
        for entity in entities:
            # Map legacy 'name' to canonical 'value'
            value = entity.get('value') or entity.get('name')
            entity_type = entity.get('type')
            normalized_value = entity.get('normalized_value')
            
            cur.execute(
                """
                INSERT INTO entities (value, type, normalized_value)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (value, entity_type, normalized_value)
            )
            result = cur.fetchone()
            if result:
                entity_id = result[0]
            else:
                cur.execute(
                    "SELECT id FROM entities WHERE value = %s AND type = %s",
                    (value, entity_type)
                )
                entity_id = cur.fetchone()[0]
            
            cur.execute(
                """
                INSERT INTO document_entities (document_id, entity_id, occurrences)
                VALUES (%s, %s, %s)
                ON CONFLICT (document_id, entity_id) DO UPDATE SET occurrences = document_entities.occurrences + 1
                """,
                (document_id, entity_id, entity.get('occurrences', 1))
            )
        conn.commit()
        cur.close()
        conn.close()

    def save_events(self, document_id, events):
        conn = self._get_connection()
        cur = conn.cursor()
        for event in events:
            cur.execute(
                """
                INSERT INTO events (timestamp, event_type, description)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (event['timestamp'], event['event_type'], event['description'])
            )
            result = cur.fetchone()
            if result:
                event_id = result[0]
            else:
                cur.execute(
                    "SELECT id FROM events WHERE timestamp = %s AND event_type = %s AND description = %s",
                    (event['timestamp'], event['event_type'], event['description'])
                )
                event_id = cur.fetchone()[0]
            
            cur.execute(
                """
                INSERT INTO document_events (document_id, event_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (document_id, event_id)
            )
        conn.commit()
        cur.close()
        conn.close()

    def save_locations(self, document_id, locations):
        conn = self._get_connection()
        cur = conn.cursor()
        for location in locations:
            cur.execute(
                """
                INSERT INTO locations (name, latitude, longitude)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (location.get('name'), location.get('latitude'), location.get('longitude'))
            )
            result = cur.fetchone()
            if result:
                location_id = result[0]
            else:
                cur.execute(
                    "SELECT id FROM locations WHERE name = %s AND latitude = %s AND longitude = %s",
                    (location.get('name'), location.get('latitude'), location.get('longitude'))
                )
                location_id = cur.fetchone()[0]
            
            cur.execute(
                """
                INSERT INTO document_locations (document_id, location_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (document_id, location_id)
            )
        conn.commit()
        cur.close()
        conn.close()

    def load_collection(self, collection_id=None, name=None):
        raise NotImplementedError()

    def search_documents(self, query=None, entity=None, date=None, month=None, location=None):
        """Search documents with optional filters.
        
        Canonical schema columns: path, extension, sha256, file_size, 
        character_count, parser, modified_time, indexed_at
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        conditions = []
        params = []
        
        # Query text search
        if query:
            conditions.append("(d.path ILIKE %s OR d.extension ILIKE %s)")
            params.extend([f"%{query}%", f"%{query}%"])
        
        # Entity filter - join with document_entities
        if entity:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM document_entities de
                    JOIN entities e ON de.entity_id = e.id
                    WHERE de.document_id = d.id AND e.value ILIKE %s
                )
            """)
            params.append(f"%{entity}%")
        
        # Date filter - documents indexed on that date
        if date:
            conditions.append("d.indexed_at::date = %s")
            params.append(date)
        
        # Month filter - documents indexed in that month
        if month:
            conditions.append("TO_CHAR(d.indexed_at, 'YYYY-MM') = %s")
            params.append(month)
        
        # Location filter - join with document_locations
        if location:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM document_locations dl
                    JOIN locations l ON dl.location_id = l.id
                    WHERE dl.document_id = d.id AND l.name ILIKE %s
                )
            """)
            params.append(f"%{location}%")
        
        # Build query - use canonical column names
        sql = """SELECT d.id, d.path, d.extension, d.sha256, d.file_size, 
                        d.character_count, d.parser, d.modified_time, d.indexed_at 
                 FROM documents d"""
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " ORDER BY d.indexed_at DESC LIMIT 100"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'path': row[1],
                'extension': row[2],
                'sha256': row[3],
                'file_size': row[4],
                'character_count': row[5],
                'parser': row[6],
                'modified_time': row[7],
                'indexed_at': row[8]
            })
        
        cur.close()
        conn.close()
        return results

    def search_entities(self, entity_type=None, value=None):
        """Search entities with optional filters.
        
        Canonical schema columns: value, type, normalized_value
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        conditions = []
        params = []
        
        if entity_type:
            conditions.append("e.type = %s")
            params.append(entity_type)
        
        if value:
            conditions.append("e.value ILIKE %s")
            params.append(f"%{value}%")
        
        sql = """
            SELECT e.id, e.type, e.value, e.normalized_value, 
                   COUNT(DISTINCT de.document_id) as doc_count
            FROM entities e
            LEFT JOIN document_entities de ON e.id = de.entity_id
        """
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " GROUP BY e.id, e.type, e.value, e.normalized_value"
        sql += " ORDER BY doc_count DESC, e.value LIMIT 100"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'type': row[1],
                'value': row[2],
                'normalized_value': row[3],
                'document_count': row[4]
            })
        
        cur.close()
        conn.close()
        return results

    def search_events(self, date=None, month=None, entity=None, event_type=None):
        """Search events with optional filters."""
        conn = self._get_connection()
        cur = conn.cursor()
        
        conditions = []
        params = []
        
        # Date filter - event on specific date
        if date:
            conditions.append("e.timestamp >= %s")
            conditions.append("e.timestamp < %s::date + INTERVAL '1 day'")
            params.append(date)
            params.append(date)
        
        # Month filter - events in specific month
        if month:
            year, mon = month.split('-')
            start_date = f"{year}-{mon}-01"
            # Calculate next month
            if mon == '12':
                next_month = f"{int(year) + 1}-01-01"
            else:
                next_month = f"{year}-{int(mon) + 1:02d}-01"
            conditions.append("e.timestamp >= %s")
            conditions.append("e.timestamp < %s")
            params.append(start_date)
            params.append(next_month)
        
        # Entity filter - events from documents containing entity
        if entity:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM document_events dev
                    JOIN document_entities de ON dev.document_id = de.document_id
                    JOIN entities ent ON de.entity_id = ent.id
                    WHERE dev.event_id = e.id AND ent.value ILIKE %s
                )
            """)
            params.append(f"%{entity}%")
        
        # Event type filter
        if event_type:
            conditions.append("e.event_type = %s")
            params.append(event_type)
        
        sql = """
            SELECT e.id, e.timestamp, e.event_type, e.description,
                   COUNT(DISTINCT dev.document_id) as doc_count
            FROM events e
            LEFT JOIN document_events dev ON e.id = dev.event_id
        """
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " GROUP BY e.id, e.timestamp, e.event_type, e.description"
        sql += " ORDER BY e.timestamp DESC LIMIT 100"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'timestamp': row[1],
                'event_type': row[2],
                'description': row[3],
                'document_count': row[4]
            })
        
        cur.close()
        conn.close()
        return results

    def search_locations(self, date=None, month=None, entity=None, location_name=None):
        """Search locations with optional filters."""
        conn = self._get_connection()
        cur = conn.cursor()
        
        conditions = []
        params = []
        
        # Date filter - locations from documents modified on that date
        if date:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM document_locations dl
                    JOIN documents d ON dl.document_id = d.id
                    WHERE dl.location_id = l.id AND d.modified_time::date = %s
                )
            """)
            params.append(date)
        
        # Month filter - locations from documents modified in that month
        if month:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM document_locations dl
                    JOIN documents d ON dl.document_id = d.id
                    WHERE dl.location_id = l.id AND TO_CHAR(d.modified_time, 'YYYY-MM') = %s
                )
            """)
            params.append(month)
        
        # Entity filter - locations from documents containing entity
        if entity:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM document_locations dl
                    JOIN document_entities de ON dl.document_id = de.document_id
                    JOIN entities ent ON de.entity_id = ent.id
                    WHERE dl.location_id = l.id AND ent.value ILIKE %s
                )
            """)
            params.append(f"%{entity}%")
        
        # Location name filter
        if location_name:
            conditions.append("l.name ILIKE %s")
            params.append(f"%{location_name}%")
        
        sql = """
            SELECT l.id, l.name, l.latitude, l.longitude,
                   COUNT(DISTINCT dl.document_id) as doc_count
            FROM locations l
            LEFT JOIN document_locations dl ON l.id = dl.location_id
        """
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " GROUP BY l.id, l.name, l.latitude, l.longitude"
        sql += " ORDER BY doc_count DESC, l.name LIMIT 100"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'name': row[1],
                'latitude': row[2],
                'longitude': row[3],
                'document_count': row[4]
            })
        
        cur.close()
        conn.close()
        return results

    def search_relationships(self, entity=None, relationship_type=None):
        """Search relationships with optional filters."""
        conn = self._get_connection()
        cur = conn.cursor()
        
        conditions = []
        params = []
        
        # Entity filter - relationships involving entity
        if entity:
            conditions.append("(r.from_entity ILIKE %s OR r.to_entity ILIKE %s)")
            params.extend([f"%{entity}%", f"%{entity}%"])
        
        # Relationship type filter
        if relationship_type:
            conditions.append("r.relationship_type = %s")
            params.append(relationship_type)
        
        sql = "SELECT id, from_entity, to_entity, relationship_type FROM relationships"
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " ORDER BY relationship_type, from_entity LIMIT 100"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'from': row[1],
                'to': row[2],
                'type': row[3]
            })
        
        cur.close()
        conn.close()
        return results