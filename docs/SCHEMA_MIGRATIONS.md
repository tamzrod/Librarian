# Schema Migration Guide

This guide explains how Librarian's forward-only PostgreSQL migrations behave during startup and where to find per-migration operational notes.

## How upgrades work

- `storage.migration_manager.MigrationManager` runs automatically during backend startup.
- Fresh databases apply every migration in order, starting with `001_initial_schema.sql`.
- Existing databases read `schema_migrations` and apply only files that have not yet been recorded.
- Each migration file runs transactionally. If a statement fails, that file is rolled back and startup stops with an error.

## Live-database expectations

- Migrations that only add new tables (`002`, `003`, `004`, `006`) are generally safe to run on a live system.
- Migrations that alter or backfill hot tables (`005`, `007`, `008`) should be scheduled during a maintenance window or with workers paused.
- `001` is a bootstrap migration for fresh installs, not a normal in-place upgrade step.

## Downgrade and rollback policy

- Librarian does not ship reverse migrations.
- To undo a failed rollout, restore a database backup taken before the upgrade.
- If the database is disposable and can be regenerated from the filesystem, `MigrationManager.reset_schema()` or `full_reset_and_rebuild()` can rebuild it from the current migration set.

## Partial upgrades

- If startup fails during a migration, only earlier successful migration files remain applied.
- The next startup retries from the first unrecorded migration because completed files stay listed in `schema_migrations`.

## Reference

- Per-migration operational notes: [`storage/migrations/CHANGELOG.md`](../storage/migrations/CHANGELOG.md)
- Migration implementation: `storage/migration_manager.py`
