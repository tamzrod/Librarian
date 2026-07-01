-- Migration: 008_document_fields.sql
-- Purpose: Add mime_type and created_at columns to documents table
-- Upgrade: Adds mime_type and created_at to documents, backfills created_at from indexed_at, and creates the mime_type index.
-- Downgrade: No automated downgrade path exists; restore from backup if the previous schema must be recovered.
-- Live DB Safety: Prefer a maintenance window or low-traffic period because ALTER TABLE plus the backfill UPDATE touches every documents row missing created_at.
-- Manual Steps: None if indexed_at is already populated. Review older rows after rollout if you need a source-of-truth created timestamp distinct from indexed_at.
--
-- The Explorer API queries these columns to display file metadata.
-- Without them, every explorer query fails silently (the except blocks catch
-- the "column does not exist" error), causing folders to appear empty.
--
-- mime_type: MIME type of the artifact (e.g., 'image/jpeg').
--            Populated by parsers/extractors; NULL until classified.
-- created_at: When the document record was first created.
--             Backfilled from indexed_at for existing records.

ALTER TABLE documents ADD COLUMN IF NOT EXISTS mime_type VARCHAR(255);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;

-- Backfill created_at from indexed_at for existing records
UPDATE documents SET created_at = indexed_at WHERE created_at IS NULL AND indexed_at IS NOT NULL;

-- Index for mime_type lookups
CREATE INDEX IF NOT EXISTS idx_documents_mime_type ON documents(mime_type);

-- Record migration
INSERT INTO schema_migrations (migration_name) VALUES ('008_document_fields.sql')
ON CONFLICT (migration_name) DO NOTHING;
