# P7 — Add Missing DB Indexes

**Source:** TD-007  
**Effort:** Low | **Risk:** Medium
**Architectural Priority:** 8 | **Implementation Order:** 9
**Hard Prerequisites:** None
**Soft Prerequisites:** P10
**Status:** ✅ Completed

---

## Problem

The `evidence_lineage` table (and possibly others) was missing indexes on its foreign-key and query columns. At scale, unindexed lookups become full table scans that block workers and degrade query latency.

## Resolution (2026-07)

- ✅ `storage/migrations/009_add_missing_indexes.sql` created
- ✅ `idx_evidence_lineage_created_at` added
- ✅ `idx_document_jobs_created_at` added
- ✅ `idx_scan_snapshots_collection` added
- ✅ Migration documented in `storage/migrations/CHANGELOG.md`

## Implementation Details

Migration 009 adds:
- `idx_evidence_lineage_created_at` on `evidence_lineage(created_at)` — eliminates full table scans in `get_entity_evidence()` and `get_document_evidence()` which both ORDER BY `created_at DESC`
- `idx_document_jobs_created_at` on `document_jobs(created_at)` — supports the worker claim query (`ORDER BY priority DESC, created_at ASC`) and all recent-jobs listings
- `idx_scan_snapshots_collection` on `scan_snapshots(collection_id)` — FK index missing from 007

All statements use `CREATE INDEX IF NOT EXISTS` for idempotency.

## Definition of Done

- ✅ `evidence_lineage` has indexes on all columns used in queries.
- ✅ Migration file `009_add_missing_indexes.sql` exists.
- ✅ `schema.sql` reflects the updated schema (via fresh-install migration).
- ✅ Migration documented in `CHANGELOG.md`.
- ✅ No existing tests are broken.
