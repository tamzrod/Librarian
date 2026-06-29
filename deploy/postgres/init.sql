-- Librarian PostgreSQL Initialization Script
--
-- This script runs automatically when the PostgreSQL container
-- is first created. It sets up the initial database schema
-- for the Librarian evidence retrieval engine.
--
-- NOTE: This is the legacy init script for first-time container setup.
-- For schema management, see storage/migrations/ directory.
-- The API will automatically ensure schema exists on startup via ensure_schema().

-- Enable UUID extension (optional, for future use)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Import the canonical schema from storage/migrations/
-- Note: Docker's entrypoint runs scripts in /docker-entrypoint-initdb.d/
-- This script now delegates to the migration file if accessible

DO $$
BEGIN
    -- Create a marker to indicate init.sql ran
    CREATE TABLE IF NOT EXISTS _librarian_init (
        initialized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        source TEXT DEFAULT 'deploy/postgres/init.sql'
    );
    
    -- Record this initialization
    INSERT INTO _librarian_init (source) VALUES ('deploy/postgres/init.sql');
EXCEPTION WHEN OTHERS THEN
    -- If we can't create the marker table, continue anyway
    -- The API's ensure_schema() will handle schema creation
    RAISE NOTICE 'Could not record init.sql execution: %', SQLERRM;
END $$;

-- Note: The actual schema tables (documents, entities, events, etc.)
-- are now created by the API's ensure_schema() method using
-- storage/migrations/schema.sql as the canonical source.
-- This ensures schema is created even if the database volume is reused.
