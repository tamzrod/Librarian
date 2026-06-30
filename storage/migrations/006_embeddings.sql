-- Migration: 006_embeddings.sql
-- Purpose: Vector embeddings and plugin registry
-- 
-- This migration adds tables for:
-- - Document vector embeddings (for semantic search)
-- - Plugin type registry

-- Document embeddings table
-- Stores vector embeddings for semantic similarity search
CREATE TABLE IF NOT EXISTS document_embeddings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE UNIQUE,
    embedding TEXT NOT NULL,  -- JSON serialized vector
    model VARCHAR(100),       -- Embedding model name (e.g., 'text-embedding-ada-002')
    dimensions INTEGER,       -- Vector dimension count
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document content table
-- Stores extracted text content from documents
CREATE TABLE IF NOT EXISTS document_content (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE UNIQUE,
    content TEXT,
    content_hash VARCHAR(64),
    character_count INTEGER,
    encoding VARCHAR(50),
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_method VARCHAR(100)
);

-- Plugin types table
-- Registry for available plugins and their job types
CREATE TABLE IF NOT EXISTS plugin_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    job_type VARCHAR(100) NOT NULL,
    description TEXT,
    version VARCHAR(50),
    enabled BOOLEAN DEFAULT TRUE,
    config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEXES
-- ============================================================

-- Document embeddings indexes
CREATE INDEX IF NOT EXISTS idx_document_embeddings_doc ON document_embeddings(document_id);

-- Document content indexes
CREATE INDEX IF NOT EXISTS idx_document_content_doc ON document_content(document_id);

-- Plugin types indexes
CREATE INDEX IF NOT EXISTS idx_plugin_types_job ON plugin_types(job_type);
CREATE INDEX IF NOT EXISTS idx_plugin_types_enabled ON plugin_types(enabled) WHERE enabled = TRUE;

-- Record migration
INSERT INTO schema_migrations (migration_name) VALUES ('006_embeddings.sql');