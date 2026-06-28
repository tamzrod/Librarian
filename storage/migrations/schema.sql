-- Collections table
CREATE TABLE IF NOT EXISTS collections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    root_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER REFERENCES collections(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    extension VARCHAR(50),
    sha256 VARCHAR(64),
    modified_time TIMESTAMP,
    file_size BIGINT,
    character_count INTEGER,
    parser VARCHAR(100),
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Entities table
CREATE TABLE IF NOT EXISTS entities (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    value TEXT NOT NULL,
    normalized_value TEXT
);

-- Document-Entity relationship table
CREATE TABLE IF NOT EXISTS document_entities (
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    occurrences INTEGER DEFAULT 1,
    PRIMARY KEY (document_id, entity_id)
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    timestamp TEXT NOT NULL,
    event_type VARCHAR(100),
    description TEXT
);

-- Document-Events relationship table
CREATE TABLE IF NOT EXISTS document_events (
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, event_id)
);

-- Locations table
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

-- Document-Locations relationship table
CREATE TABLE IF NOT EXISTS document_locations (
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    location_id INTEGER REFERENCES locations(id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, location_id)
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_documents_collection ON documents(collection_id);
CREATE INDEX IF NOT EXISTS idx_documents_path ON documents(path);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_value ON entities(value);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_locations_name ON locations(name);
CREATE INDEX IF NOT EXISTS idx_locations_coords ON locations(latitude, longitude);