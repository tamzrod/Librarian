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

    def search_documents(self, query, collection_id=None):
        raise NotImplementedError()

    def search_entities(self, entity_type=None, value=None):
        raise NotImplementedError()