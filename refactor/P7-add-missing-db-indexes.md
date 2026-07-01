# P7 — Add Missing DB Indexes

**Source:** TD-007  
**Effort:** Low | **Risk:** Medium | **Priority:** 7

---

## Problem

The `evidence_lineage` table (and possibly others) is missing indexes on its foreign-key and query columns. At scale, unindexed lookups become full table scans that block workers and degrade query latency.

## Impact

- Slow evidence queries as the library grows.
- Worker throughput degrades because evidence lineage lookups block job completion.
- Schema migration risk increases — adding indexes later on a large table requires `CREATE INDEX CONCURRENTLY` and maintenance windows.

## Files Affected

| File | Action |
|------|--------|
| `storage/migrations/schema.sql` | Add index definitions |
| `storage/migrations/` | Add a new migration file (e.g. `006_add_evidence_lineage_indexes.sql`) |

## Steps

1. Audit `evidence_lineage` columns used in `WHERE` clauses or `JOIN` conditions across the codebase (`grep -r evidence_lineage`).
2. Add indexes for:
   - `evidence_lineage.document_id` (FK lookup)
   - `evidence_lineage.entity_id` (if queried)
   - `evidence_lineage.created_at` (range queries)
3. Audit other tables for missing FK indexes (check `document_jobs.document_id`, `document_content.document_id`, etc.).
4. Write a new migration file that applies the indexes using `CREATE INDEX IF NOT EXISTS`.
5. Use `CREATE INDEX CONCURRENTLY` in the migration if the table could be large when the migration runs.
6. Update `schema.sql` to include the indexes so fresh installs get them too.

## Definition of Done

- `evidence_lineage` has indexes on all columns used in queries.
- A migration file exists for the new indexes.
- `schema.sql` reflects the updated schema.
- No existing tests are broken.
