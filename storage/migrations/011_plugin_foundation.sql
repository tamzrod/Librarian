-- Migration: 011_plugin_foundation.sql
-- Operation Plugin Foundation
-- Purpose: Add plugin identity and provenance columns to observation tables
-- Safety: Safe on live database (additive changes with backfill)
-- Rollback: Available via DROP COLUMN statements
-- Date: 2026-07-05

-- Operation Plugin Foundation establishes:
-- 1. Plugin Identity: Every observation attributable to plugin_name, engine_name, plugin_version
-- 2. Provenance: Every observation includes processed_at timestamp
-- 3. Namespacing: Convention for plugin naming (e.g., metadata.exif.pillow)
-- 4. Multi-Engine Readiness: UNIQUE constraint allows multiple engines per document

-- =============================================================================
-- STEP 1: Add identity and provenance columns to photo_metadata
-- =============================================================================

-- Add columns (nullable first to allow backfill)
ALTER TABLE photo_metadata
    ADD COLUMN IF NOT EXISTS plugin_name VARCHAR(100);
ALTER TABLE photo_metadata
    ADD COLUMN IF NOT EXISTS engine_name VARCHAR(100);
ALTER TABLE photo_metadata
    ADD COLUMN IF NOT EXISTS plugin_version VARCHAR(50);
ALTER TABLE photo_metadata
    ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;
ALTER TABLE photo_metadata
    ADD COLUMN IF NOT EXISTS artifact_hash VARCHAR(64);

-- =============================================================================
-- STEP 2: Backfill existing rows with default values
-- =============================================================================

-- Set DEFAULT values for existing rows
UPDATE photo_metadata
SET 
    plugin_name = 'metadata.exif.pillow',
    engine_name = 'pillow-exif',
    plugin_version = '1.0.0',
    processed_at = COALESCE(extracted_at, CURRENT_TIMESTAMP)
WHERE plugin_name IS NULL;

-- =============================================================================
-- STEP 3: Set NOT NULL constraints after backfill
-- =============================================================================

ALTER TABLE photo_metadata
    ALTER COLUMN plugin_name SET NOT NULL,
    ALTER COLUMN engine_name SET NOT NULL,
    ALTER COLUMN plugin_version SET NOT NULL,
    ALTER COLUMN processed_at SET NOT NULL;

-- Set DEFAULT values for future inserts
ALTER TABLE photo_metadata
    ALTER COLUMN plugin_name SET DEFAULT 'metadata.exif.pillow',
    ALTER COLUMN engine_name SET DEFAULT 'pillow-exif',
    ALTER COLUMN plugin_version SET DEFAULT '1.0.0',
    ALTER COLUMN processed_at SET DEFAULT CURRENT_TIMESTAMP;

-- =============================================================================
-- STEP 4: Update UNIQUE constraint for multi-engine support
-- =============================================================================

-- Remove old UNIQUE constraint that prevents multiple engines
ALTER TABLE photo_metadata 
    DROP CONSTRAINT IF EXISTS photo_metadata_document_id_key;

-- Add new multi-engine UNIQUE constraint
-- This allows multiple engines per document (future-proofing)
-- Each plugin+engine combination can have one observation per document
ALTER TABLE photo_metadata 
    ADD CONSTRAINT uq_photo_metadata_identity
    UNIQUE (document_id, plugin_name, engine_name);

-- =============================================================================
-- STEP 5: Add indexes for provenance queries
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_photo_metadata_plugin
    ON photo_metadata(plugin_name);
CREATE INDEX IF NOT EXISTS idx_photo_metadata_engine
    ON photo_metadata(engine_name);
CREATE INDEX IF NOT EXISTS idx_photo_metadata_version
    ON photo_metadata(plugin_version);
CREATE INDEX IF NOT EXISTS idx_photo_metadata_processed
    ON photo_metadata(processed_at DESC);

-- =============================================================================
-- STEP 6: Apply to entities table
-- =============================================================================

ALTER TABLE entities
    ADD COLUMN IF NOT EXISTS plugin_name VARCHAR(100) DEFAULT 'entity-extractor';
ALTER TABLE entities
    ADD COLUMN IF NOT EXISTS engine_name VARCHAR(100) DEFAULT 'spacy';
ALTER TABLE entities
    ADD COLUMN IF NOT EXISTS plugin_version VARCHAR(50) DEFAULT '1.0.0';
ALTER TABLE entities
    ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Backfill
UPDATE entities
SET 
    plugin_name = 'entity-extractor',
    engine_name = 'spacy',
    plugin_version = '1.0.0',
    processed_at = CURRENT_TIMESTAMP
WHERE plugin_name IS NULL;

ALTER TABLE entities
    ALTER COLUMN plugin_name SET NOT NULL,
    ALTER COLUMN engine_name SET NOT NULL,
    ALTER COLUMN plugin_version SET NOT NULL,
    ALTER COLUMN processed_at SET NOT NULL;

ALTER TABLE entities
    ALTER COLUMN plugin_name SET DEFAULT 'entity-extractor',
    ALTER COLUMN engine_name SET DEFAULT 'spacy',
    ALTER COLUMN plugin_version SET DEFAULT '1.0.0',
    ALTER COLUMN processed_at SET DEFAULT CURRENT_TIMESTAMP;

-- =============================================================================
-- STEP 7: Apply to document_content table
-- =============================================================================

ALTER TABLE document_content
    ADD COLUMN IF NOT EXISTS plugin_name VARCHAR(100) DEFAULT 'text-extractor';
ALTER TABLE document_content
    ADD COLUMN IF NOT EXISTS engine_name VARCHAR(100) DEFAULT 'textract';
ALTER TABLE document_content
    ADD COLUMN IF NOT EXISTS plugin_version VARCHAR(50) DEFAULT '1.0.0';
ALTER TABLE document_content
    ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Backfill
UPDATE document_content
SET 
    plugin_name = 'text-extractor',
    engine_name = 'textract',
    plugin_version = '1.0.0',
    processed_at = COALESCE(extracted_at, CURRENT_TIMESTAMP)
WHERE plugin_name IS NULL;

ALTER TABLE document_content
    ALTER COLUMN plugin_name SET NOT NULL,
    ALTER COLUMN engine_name SET NOT NULL,
    ALTER COLUMN plugin_version SET NOT NULL,
    ALTER COLUMN processed_at SET NOT NULL;

ALTER TABLE document_content
    ALTER COLUMN plugin_name SET DEFAULT 'text-extractor',
    ALTER COLUMN engine_name SET DEFAULT 'textract',
    ALTER COLUMN plugin_version SET DEFAULT '1.0.0',
    ALTER COLUMN processed_at SET DEFAULT CURRENT_TIMESTAMP;

-- =============================================================================
-- STEP 8: Apply to document_embeddings table
-- =============================================================================

ALTER TABLE document_embeddings
    ADD COLUMN IF NOT EXISTS plugin_name VARCHAR(100) DEFAULT 'embeddings';
ALTER TABLE document_embeddings
    ADD COLUMN IF NOT EXISTS engine_name VARCHAR(100);
ALTER TABLE document_embeddings
    ADD COLUMN IF NOT EXISTS plugin_version VARCHAR(50) DEFAULT '1.0.0';
ALTER TABLE document_embeddings
    ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Backfill
UPDATE document_embeddings
SET 
    plugin_name = 'embeddings',
    plugin_version = '1.0.0',
    processed_at = COALESCE(created_at, CURRENT_TIMESTAMP)
WHERE plugin_name IS NULL;

ALTER TABLE document_embeddings
    ALTER COLUMN plugin_name SET NOT NULL,
    ALTER COLUMN plugin_version SET NOT NULL,
    ALTER COLUMN processed_at SET NOT NULL;

ALTER TABLE document_embeddings
    ALTER COLUMN plugin_name SET DEFAULT 'embeddings',
    ALTER COLUMN plugin_version SET DEFAULT '1.0.0',
    ALTER COLUMN processed_at SET DEFAULT CURRENT_TIMESTAMP;

-- =============================================================================
-- STEP 9: Update evidence_lineage table
-- =============================================================================

-- Ensure plugin_name is not nullable
ALTER TABLE evidence_lineage
    ALTER COLUMN plugin_name SET NOT NULL;

-- =============================================================================
-- STEP 10: Add comments for documentation
-- =============================================================================

COMMENT ON COLUMN photo_metadata.plugin_name IS 
    'Plugin that produced this observation (e.g., metadata.exif.pillow)';
COMMENT ON COLUMN photo_metadata.engine_name IS 
    'Engine used by plugin (e.g., pillow-exif)';
COMMENT ON COLUMN photo_metadata.plugin_version IS 
    'Version of the plugin (e.g., 1.0.0)';
COMMENT ON COLUMN photo_metadata.processed_at IS 
    'When this observation was created';
COMMENT ON COLUMN photo_metadata.artifact_hash IS 
    'SHA256 hash of source artifact for integrity';

-- =============================================================================
-- STEP 11: Record migration
-- =============================================================================

INSERT INTO schema_migrations (migration_name)
VALUES ('011_plugin_foundation.sql');
