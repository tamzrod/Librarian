-- Migration: 007_job_orchestration.sql
-- Purpose: Job orchestration improvements
--
-- This migration adds:
-- 1. BLOCKED status for jobs waiting on prerequisites
-- 2. Job prerequisites table for dependency tracking
-- 3. Worker versions tracking for scan idempotency
-- 4. Scan snapshots for deduplication

-- Add BLOCKED status to job status enum
-- Note: In PostgreSQL, we use CHECK constraint for status values
ALTER TABLE document_jobs DROP CONSTRAINT IF EXISTS chk_job_status;
ALTER TABLE document_jobs ADD CONSTRAINT chk_job_status 
    CHECK (status IN ('QUEUED', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED', 'FAILED_PERMANENT', 'CANCELLED'));

-- Create job_prerequisites table for dependency tracking
CREATE TABLE IF NOT EXISTS job_prerequisites (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(100) NOT NULL,
    requires_job_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_job_prerequisite UNIQUE (job_type, requires_job_type)
);

-- Create index for looking up prerequisites
CREATE INDEX IF NOT EXISTS idx_job_prerequisites_job ON job_prerequisites(job_type);

-- Insert default job dependencies
-- extract_entities, extract_locations, generate_embeddings all require extract_text first
INSERT INTO job_prerequisites (job_type, requires_job_type) VALUES
    ('extract_entities', 'extract_text'),
    ('extract_locations', 'extract_text'),
    ('generate_embeddings', 'extract_text')
ON CONFLICT DO NOTHING;

-- Create scan_snapshots table for tracking processed files
-- This enables idempotent rescans
CREATE TABLE IF NOT EXISTS scan_snapshots (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER REFERENCES collections(id) ON DELETE CASCADE,
    scan_path TEXT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    artifact_type VARCHAR(50),
    worker_version VARCHAR(100),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_scan_snapshot UNIQUE (scan_path, file_hash)
);

-- Create index for lookups
CREATE INDEX IF NOT EXISTS idx_scan_snapshots_path ON scan_snapshots(scan_path);
CREATE INDEX IF NOT EXISTS idx_scan_snapshots_hash ON scan_snapshots(file_hash);

-- Add worker_version column to track when jobs need regeneration
ALTER TABLE document_jobs ADD COLUMN IF NOT EXISTS worker_version VARCHAR(100);

-- Add scan_snapshot_id for tracking which scan created a job
ALTER TABLE document_jobs ADD COLUMN IF NOT EXISTS scan_snapshot_id INTEGER 
    REFERENCES scan_snapshots(id) ON DELETE SET NULL;

-- Record migration
INSERT INTO schema_migrations (migration_name) VALUES ('007_job_orchestration.sql');
