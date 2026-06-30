-- Migration: 004_test.sql
-- Test migration for filesystem-based migration framework verification
-- Purpose: Verify that migrations are discovered and applied correctly

-- Create a simple test table to verify migration was applied
CREATE TABLE IF NOT EXISTS migration_test (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verification_value VARCHAR(255) DEFAULT 'migration_framework_test'
);

-- Insert a verification record
INSERT INTO migration_test (migration_name, verification_value)
VALUES ('004_test.sql', 'filesystem_migration_framework_working');

-- Record migration
INSERT INTO schema_migrations (migration_name) VALUES ('004_test.sql');
