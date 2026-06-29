import psycopg
from .backend import StorageBackend


class PostgresBackend(StorageBackend):
    def __init__(self, host='localhost', port=5432, dbname='librarian',
                 user='librarian', password='librarian'):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self._connection = None

    def _get_connection(self):
        return psycopg.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password
        )

    def _ensure_schema(self):
        with open('storage/migrations/schema.sql', 'r') as f:
            schema = f.read()
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(schema)
        conn.commit()
        cur.close()
        conn.close()

    def save_collection(self, collection):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO collections (name, root_path, created_at)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (collection['name'], collection['root_path'], collection.get('created_at'))
        )
        collection_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return collection_id

    def save_document(self, document):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO documents (collection_id, path, extension, sha256, modified_time, file_size, character_count, parser, indexed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                document.get('collection_id'),
                document.get('path'),
                document.get('extension'),
                document.get('sha256'),
                document.get('modified_time'),
                document.get('file_size'),
                document.get('character_count'),
                document.get('parser'),
                document.get('indexed_at')
            )
        )
        document_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return document_id

    def save_entities(self, document_id, entities):
        conn = self._get_connection()
        cur = conn.cursor()
        for entity in entities:
            cur.execute(
                """
                INSERT INTO entities (type, value, normalized_value)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (entity['type'], entity['value'], entity.get('normalized_value'))
            )
            result = cur.fetchone()
            if result:
                entity_id = result[0]
            else:
                cur.execute(
                    "SELECT id FROM entities WHERE type = %s AND value = %s",
                    (entity['type'], entity['value'])
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
        """Search documents with optional filters."""
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
        
        # Date filter - documents modified on that date
        if date:
            conditions.append("d.modified_time::date = %s")
            params.append(date)
        
        # Month filter - documents modified in that month
        if month:
            conditions.append("TO_CHAR(d.modified_time, 'YYYY-MM') = %s")
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
        
        # Build query
        sql = "SELECT d.id, d.path, d.extension, d.modified_time, d.file_size FROM documents d"
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " ORDER BY d.modified_time DESC LIMIT 100"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'path': row[1],
                'extension': row[2],
                'modified_time': row[3],
                'file_size': row[4]
            })
        
        cur.close()
        conn.close()
        return results

    def search_entities(self, entity_type=None, value=None):
        """Search entities with optional filters."""
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