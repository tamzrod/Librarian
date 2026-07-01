-- Migration: 009_add_missing_indexes.sql
-- Purpose: Add missing indexes on query-critical columns
-- Upgrade: Adds indexes on evidence_lineage.created_at, document_jobs.created_at,
--          and scan_snapshots.collection_id. Uses CREATE INDEX IF NOT EXISTS for
--          idempotency.
-- Downgrade: No automated downgrade path exists. Restore from backup or reset/rebuild
--            the disposable catalog.
-- Live DB Safety: Safe on a live database because it only creates new indexes, though
--                 a brief metadata lock is expected during index creation. For very large
--                 tables in production use CREATE INDEX CONCURRENTLY outside of a
--                 transaction to avoid blocking reads/writes.
-- Manual Steps: None for normal deployments. In high-traffic environments, apply
--               manually with CREATE INDEX CONCURRENTLY and then mark this migration
--               as applied by inserting its name into schema_migrations.
--
-- Indexes added by this migration:
--
-- 1. evidence_lineage.created_at
--    Both get_entity_evidence() and get_document_evidence() in PostgresBackend
--    ORDER BY e.created_at DESC. Without this index, each call is a full table scan
--    that grows with every entity-extraction run.
--
-- 2. document_jobs.created_at
--    The worker claim query (ORDER BY priority DESC, created_at ASC) and every
--    recent-jobs listing in api/routes/operations.py and api/routes/pipeline.py
--    sort or filter on created_at. An index reduces queue-claim latency as the
--    job table grows.
--
-- 3. scan_snapshots.collection_id
--    Foreign key to collections(id). Standard FK index to support ON DELETE CASCADE
--    and any future collection-scoped snapshot lookups.

-- Evidence lineage: ORDER BY created_at DESC used by get_entity_evidence()
-- and get_document_evidence() in PostgresBackend.
CREATE INDEX IF NOT EXISTS idx_evidence_lineage_created_at
    ON evidence_lineage(created_at);

-- Document jobs: ORDER BY priority DESC, created_at ASC used by worker claim
-- query: ORDER BY created_at DESC or ASC used by operations and pipeline routes
CREATE INDEX IF NOT EXISTS idx_document_jobs_created_at
    ON document_jobs(created_at);

-- Scan snapshots: collection_id FK column. No index was created in 007.
CREATE INDEX IF NOT EXISTS idx_scan_snapshots_collection
    ON scan_snapshots(collection_id);

-- Record migration
INSERT INTO schema_migrations (migration_name) VALUES ('009_add_missing_indexes.sql')
ON CONFLICT (migration_name) DO NOTHING;
