-- Migration: 005_artifact_inventory.sql
-- Purpose: Artifact Inventory Architecture
-- Upgrade: Adds artifact inventory columns to documents, creates artifact_type_enum, backfills existing rows, and adds lifecycle/deletion indexes.
-- Downgrade: No automated downgrade path exists. Restore from backup if the previous schema must be recovered.
-- Live DB Safety: Run during a maintenance window or low-traffic period because ALTER TABLE and backfill UPDATE statements lock and rewrite rows in documents.
-- Manual Steps: Verify workers tolerate the new columns before rollout. No manual data backfill is required beyond the statements in this migration.
-- 
-- This migration implements the core principle: Discovery precedes understanding.
-- The database becomes the canonical inventory of known artifacts.
-- A file does not require a parser to exist as an artifact.
--
-- FILESYSTEM = SOURCE OF TRUTH
-- DATABASE = REGENERATABLE CACHE
--
-- Changes:
-- 1. Add artifact_type column for classification
-- 2. Add exists_on_disk column for soft deletion tracking
-- 3. Add deleted_at column for audit trail
-- 4. Add lifecycle_state column for simplified lifecycle tracking
-- 5. Create artifact_type_enum for standardized types

-- Create artifact type enum
-- These types classify artifacts based on their nature
DO $$ BEGIN
    CREATE TYPE artifact_type_enum AS ENUM (
        'unknown',      -- Default for undiscovered/unclassified artifacts
        'image',        -- Photos, graphics
        'document',     -- PDFs, office docs, text files
        'video',        -- Movies, recordings
        'audio',        -- Music, voice recordings
        'archive',      -- ZIPs, tarballs, compressed files
        'structured',   -- CSV, JSON, XML, databases
        'executable',   -- Binaries, scripts
        'other'         -- Catch-all for known but uncategorized
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add artifact_type column to documents table
-- This column classifies the artifact type
-- Default is 'unknown' - artifacts exist before classification
ALTER TABLE documents ADD COLUMN IF NOT EXISTS artifact_type artifact_type_enum DEFAULT 'unknown';

-- Add exists_on_disk column to documents table
-- This column tracks whether the artifact still exists on disk
-- Default is TRUE - new artifacts are assumed to exist
ALTER TABLE documents ADD COLUMN IF NOT EXISTS exists_on_disk BOOLEAN DEFAULT TRUE;

-- Add deleted_at column to documents table
-- This column records when the artifact was deleted from disk
-- NULL means the artifact still exists on disk
ALTER TABLE documents ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- Add lifecycle_state column for simplified lifecycle tracking
-- This provides a higher-level view of artifact state
-- Lifecycle states: discovered -> classified -> enriched
ALTER TABLE documents ADD COLUMN IF NOT EXISTS lifecycle_state VARCHAR(50) DEFAULT 'discovered';

-- Create index for querying by artifact type
CREATE INDEX IF NOT EXISTS idx_documents_artifact_type ON documents(artifact_type);

-- Create index for querying deleted artifacts
CREATE INDEX IF NOT EXISTS idx_documents_exists_on_disk ON documents(exists_on_disk) WHERE exists_on_disk = FALSE;

-- Create index for lifecycle state queries
CREATE INDEX IF NOT EXISTS idx_documents_lifecycle_state ON documents(lifecycle_state);

-- Update existing documents with 'unknown' artifact_type where not already set
-- This preserves existing data while applying the new model
UPDATE documents SET artifact_type = 'unknown' WHERE artifact_type IS NULL;

-- Update existing documents with lifecycle_state = 'discovered' where status is DISCOVERED
-- This maps existing DISCOVERED status to the new lifecycle model
UPDATE documents SET lifecycle_state = 'discovered' WHERE status = 'DISCOVERED' AND lifecycle_state IS NULL;

-- Comment documentation
COMMENT ON COLUMN documents.artifact_type IS 'Classifies artifact type: unknown, image, document, video, audio, archive, structured, executable, other';
COMMENT ON COLUMN documents.exists_on_disk IS 'FALSE when file is deleted from disk. Preserves record for audit.';
COMMENT ON COLUMN documents.deleted_at IS 'Timestamp when file was deleted from disk. NULL if file exists.';
COMMENT ON COLUMN documents.lifecycle_state IS 'Simplified lifecycle: discovered, classified, enriched. Independent of individual job status.';

-- Record migration
INSERT INTO schema_migrations (migration_name) VALUES ('005_artifact_inventory.sql');
