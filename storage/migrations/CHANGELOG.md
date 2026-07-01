# Schema Migration Changelog

This changelog documents every forward-only schema migration in `storage/migrations/` and how the current `MigrationManager` applies them.

## Upgrade Behaviour

- Migrations run automatically at startup through `storage.migration_manager.MigrationManager`.
- Fresh databases apply migrations in numeric order beginning with `001_initial_schema.sql`.
- Existing databases skip entries already recorded in `schema_migrations` and apply only pending files.
- Each migration file executes in a single transaction. If any statement fails, that file is rolled back and is not recorded as applied.

## Partial Application and Recovery

- Partial upgrades are expected to recover cleanly on the next startup because previously recorded migrations are skipped and pending files are retried.
- A failed migration stops the run at the first error; later migrations are not attempted.
- There is no per-migration downgrade support. Roll back by restoring a database backup, or use `MigrationManager.reset_schema()` / `full_reset_and_rebuild()` only when the database can be regenerated from the filesystem.

## Migration Summary

| Migration | Upgrade Summary | Live-DB Safety | Manual Steps |
|---|---|---|---|
| `001_initial_schema.sql` | Creates `schema_migrations`, `collections`, `documents`, and `document_jobs`. | Fresh-install safe; not a normal live-upgrade step. | None for new installs. |
| `002_entities.sql` | Adds entity, relationship, document-entity, and evidence-lineage tables plus indexes. | Safe on live systems; creates new tables only. | None. |
| `003_photo_metadata.sql` | Adds `photo_metadata` and related indexes/comments for EXIF timeline data. | Safe on live systems; creates new table only. | None. |
| `004_timeline.sql` | Adds event/location timeline tables and join tables plus indexes. | Safe on live systems; creates new tables only. | None. |
| `005_artifact_inventory.sql` | Adds artifact inventory columns to `documents`, creates `artifact_type_enum`, and backfills existing rows. | Maintenance-window recommended because `documents` is altered and backfilled. | Ensure workers understand the new columns before rollout. |
| `006_embeddings.sql` | Adds embeddings, extracted content, and plugin registry tables plus indexes. | Safe on live systems; creates new tables only. | None. |
| `007_job_orchestration.sql` | Expands job status checks, adds prerequisite/snapshot tables, seeds defaults, and extends `document_jobs`. | Maintenance-window recommended because queue writes can conflict with `document_jobs` changes. | Pause workers before applying. |
| `008_document_fields.sql` | Adds `mime_type` and `created_at` to `documents`, backfills `created_at`, and indexes `mime_type`. | Maintenance-window recommended because `documents` is altered and backfilled. | None. |

## Detailed Notes

### 001_initial_schema.sql

- Intended for fresh database bootstrap.
- Establishes the minimum schema required for application startup and queueing.

### 002_entities.sql

- Introduces extracted entities and their provenance relationships.
- Safe to apply after the base schema because it does not rewrite existing `documents` rows.

### 003_photo_metadata.sql

- Adds EXIF-focused storage used by the evidence timeline.
- Safe to apply incrementally because existing tables are unchanged.

### 004_timeline.sql

- Adds temporal and geospatial timeline support tables.
- Safe to apply incrementally because existing tables are unchanged.

### 005_artifact_inventory.sql

- Converts `documents` toward the artifact-inventory model by adding classification and soft-delete fields.
- Backfill statements rely on the existing `status`/`indexed_at` data in `documents`.

### 006_embeddings.sql

- Adds storage for extracted content and semantic-search embeddings.
- Safe to apply incrementally because existing tables are unchanged.

### 007_job_orchestration.sql

- Changes queue behavior by introducing `BLOCKED` jobs and prerequisite tracking.
- Apply while workers are stopped so no process observes mixed pre/post-migration job semantics.

### 008_document_fields.sql

- Adds fields required by Explorer API file metadata responses.
- Existing rows inherit `created_at` from `indexed_at`; review that mapping if historical ingest time differs from desired record-creation semantics.
