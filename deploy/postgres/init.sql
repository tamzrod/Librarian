-- Librarian PostgreSQL Initialization Script
--
-- This script runs automatically when the PostgreSQL container
-- is first created. It sets up the initial database schema
-- for the Librarian evidence retrieval engine.

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Documents table: stores indexed file metadata
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    extension TEXT,
    size_bytes BIGINT,
    hash TEXT,
    parser TEXT,
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Entities table: stores extracted named entities
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT,  -- person, organization, device, etc.
    confidence FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Events table: stores timestamped occurrences
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Locations table: stores geographic data
CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    gps_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Relationships table: stores connections between entities
CREATE TABLE IF NOT EXISTS relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_entity_id, target_entity_id, relationship_type)
);

-- Full-text search index on documents
CREATE INDEX IF NOT EXISTS idx_documents_name_fts ON documents USING GIN (
    to_tsvector('english', name || ' ' || COALESCE(path, ''))
);

-- Index on entities for fast lookup
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities USING GIN (to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);

-- Index on events for temporal queries
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);

-- Index on locations for geospatial queries
CREATE INDEX IF NOT EXISTS idx_locations_coords ON locations(latitude, longitude);

-- Index on relationships
CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_entity_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.metadata IS DISTINCT FROM OLD.metadata THEN
        NEW.metadata = JSONB_SET(COALESCE(NEW.metadata, '{}'), '{updated_at}', to_jsonb(NOW()));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE documents IS 'Indexed artifacts with extracted metadata';
COMMENT ON TABLE entities IS 'Named things discovered in artifacts (people, organizations, devices)';
COMMENT ON TABLE events IS 'Timestamped occurrences extracted from artifacts';
COMMENT ON TABLE locations IS 'Geographic points or named places from artifacts';
COMMENT ON TABLE relationships IS 'Connections between entities in artifacts';
