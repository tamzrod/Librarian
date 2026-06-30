-- Migration: 001_initial_schema.sql
-- Purpose: Core tables required for Librarian operation
-- 
-- This migration contains ONLY tables absolutely required for startup:
-- - schema_migrations (internal tracking)
-- - collections (directory organization)
-- - documents (artifact inventory)
-- - document_jobs (work queue)
--
-- All other tables are in subsequent migrations to support:
-- - Migration-only architecture
-- - Incremental schema evolution
-- - Fresh database bootstrap

-- Schema migrations tracking table
-- This table MUST be created first as it tracks all migrations
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Collections table
-- Groups directories for organization
CREATE TABLE IF NOT EXISTS collections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    root_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents table (Artifact Inventory)
-- The canonical inventory of known artifacts.
-- A file does not require a parser to exist as an artifact.
-- 
-- FILESYSTEM = SOURCE OF TRUTH
-- DATABASE = REGENERATABLE CACHE
--
-- If database is deleted, Librarian rebuilds from filesystem.
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER REFERENCES collections(id) ON DELETE CASCADE,
    
    -- Artifact identification
    path TEXT NOT NULL UNIQUE,
    extension VARCHAR(50),
    sha256 VARCHAR(64),
    
    -- File metadata
    modified_time TIMESTAMP,
    file_size BIGINT,
    
    -- Processing metadata
    character_count INTEGER,
    parser VARCHAR(100),
    
    -- Document processing lifecycle state
    -- Status transitions: DISCOVERED -> METADATA_INDEXED -> CONTENT_EXTRACTED 
    --                    -> ENTITY_EXTRACTED -> RELATIONSHIPS_BUILT -> EMBEDDED -> COMPLETE
    status VARCHAR(50) NOT NULL DEFAULT 'DISCOVERED',
    status_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_error TEXT,
    attempt_count INTEGER DEFAULT 0,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document jobs table (Work Queue)
-- Manages processing tasks for documents
CREATE TABLE IF NOT EXISTS document_jobs (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    job_type VARCHAR(100) NOT NULL,
    priority INTEGER DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'QUEUED',
    
    -- Lease management for crash recovery
    claimed_at TIMESTAMP,
    lease_until TIMESTAMP,
    
    -- Retry support (exponential backoff)
    attempt_count INTEGER DEFAULT 0,
    last_error TEXT,
    next_retry_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    worker_id VARCHAR(100),
    error_message TEXT,
    
    -- Unique constraint: one job per document per type
    CONSTRAINT uq_document_job UNIQUE (document_id, job_type)
);

-- ============================================================
-- INDEXES (Core)
-- ============================================================

-- Documents indexes
CREATE INDEX IF NOT EXISTS idx_documents_collection ON documents(collection_id);
CREATE INDEX IF NOT EXISTS idx_documents_path ON documents(path);
CREATE INDEX IF NOT EXISTS idx_documents_extension ON documents(extension);
CREATE INDEX IF NOT EXISTS idx_documents_modified_time ON documents(modified_time);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);

-- Document jobs indexes
CREATE INDEX IF NOT EXISTS idx_document_jobs_document ON document_jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_document_jobs_status ON document_jobs(status);
CREATE INDEX IF NOT EXISTS idx_document_jobs_type ON document_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_document_jobs_priority ON document_jobs(priority);
CREATE INDEX IF NOT EXISTS idx_document_jobs_lease ON document_jobs(lease_until) WHERE status = 'IN_PROGRESS';
CREATE INDEX IF NOT EXISTS idx_document_jobs_retry ON document_jobs(next_retry_at) WHERE status = 'QUEUED';

-- Record migration
INSERT INTO schema_migrations (migration_name) VALUES ('001_initial_schema.sql');