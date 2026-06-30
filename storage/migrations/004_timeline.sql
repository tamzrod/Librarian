-- Migration: 004_timeline.sql
-- Purpose: Timeline and temporal data tracking
-- 
-- This migration adds tables for:
-- - Event extraction and temporal tracking
-- - Location extraction and geocoding
-- - Document-event and document-location relationships

-- Events table
-- Stores extracted events with temporal information
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    timestamp TEXT NOT NULL,
    event_type VARCHAR(100),
    description TEXT
);

-- Document-Events relationship table
-- Links documents to the events they reference
CREATE TABLE IF NOT EXISTS document_events (
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, event_id)
);

-- Locations table
-- Stores extracted locations with optional geocoding
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

-- Document-Locations relationship table
-- Links documents to the locations they reference
CREATE TABLE IF NOT EXISTS document_locations (
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    location_id INTEGER REFERENCES locations(id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, location_id)
);

-- ============================================================
-- INDEXES
-- ============================================================

-- Events indexes
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);

-- Locations indexes
CREATE INDEX IF NOT EXISTS idx_locations_name ON locations(name);
CREATE INDEX IF NOT EXISTS idx_locations_coords ON locations(latitude, longitude);

-- Junction table indexes (for efficient JOINs)
CREATE INDEX IF NOT EXISTS idx_document_events_doc ON document_events(document_id);
CREATE INDEX IF NOT EXISTS idx_document_events_evt ON document_events(event_id);
CREATE INDEX IF NOT EXISTS idx_document_locations_doc ON document_locations(document_id);
CREATE INDEX IF NOT EXISTS idx_document_locations_loc ON document_locations(location_id);

-- Record migration
INSERT INTO schema_migrations (migration_name) VALUES ('004_timeline.sql');