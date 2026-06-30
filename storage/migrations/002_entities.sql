-- Migration: 002_entities.sql
-- Purpose: Entity extraction and relationship tracking
-- 
-- This migration adds tables for:
-- - Entity storage and classification
-- - Entity-document relationships
-- - Relationship tracking between entities

-- Entities table
-- Stores extracted entities (people, organizations, concepts, etc.)
CREATE TABLE IF NOT EXISTS entities (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    value TEXT NOT NULL,
    normalized_value TEXT
);

-- Relationships table
-- Stores relationships between entities
CREATE TABLE IF NOT EXISTS relationships (
    id SERIAL PRIMARY KEY,
    from_entity TEXT NOT NULL,
    to_entity TEXT NOT NULL,
    relationship_type VARCHAR(100)
);

-- Document-Entity relationship table
-- Links documents to the entities they contain
CREATE TABLE IF NOT EXISTS document_entities (
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    occurrences INTEGER DEFAULT 1,
    PRIMARY KEY (document_id, entity_id)
);

-- Evidence lineage table (Phase 5: provenance tracking)
-- Tracks: entity → derived_from → document → derived_from → artifact
CREATE TABLE IF NOT EXISTS evidence_lineage (
    id SERIAL PRIMARY KEY,
    entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    artifact_path TEXT,
    plugin_name VARCHAR(100),
    confidence DOUBLE PRECISION DEFAULT 1.0,
    processing_time_ms INTEGER,
    version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEXES
-- ============================================================

-- Entities indexes
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_value ON entities(value);
CREATE INDEX IF NOT EXISTS idx_entities_normalized ON entities(normalized_value);

-- Relationships indexes
CREATE INDEX IF NOT EXISTS idx_relationships_from ON relationships(from_entity);
CREATE INDEX IF NOT EXISTS idx_relationships_to ON relationships(to_entity);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type);

-- Junction table indexes (for efficient JOINs)
CREATE INDEX IF NOT EXISTS idx_document_entities_doc ON document_entities(document_id);
CREATE INDEX IF NOT EXISTS idx_document_entities_ent ON document_entities(entity_id);

-- Evidence lineage indexes
CREATE INDEX IF NOT EXISTS idx_evidence_entity ON evidence_lineage(entity_id);
CREATE INDEX IF NOT EXISTS idx_evidence_document ON evidence_lineage(document_id);
CREATE INDEX IF NOT EXISTS idx_evidence_plugin ON evidence_lineage(plugin_name);

-- Record migration
INSERT INTO schema_migrations (migration_name) VALUES ('002_entities.sql');