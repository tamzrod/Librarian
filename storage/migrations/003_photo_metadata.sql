-- Migration: 003_photo_metadata.sql
-- Phase 1A: Photo Metadata Extraction
-- Purpose: Store extracted EXIF metadata from image files for Evidence Timeline

-- Photo metadata table
-- Stores deterministic metadata extracted from image EXIF data
CREATE TABLE IF NOT EXISTS photo_metadata (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE UNIQUE,
    
    -- Timestamp metadata
    timestamp_original TIMESTAMP,
    timestamp_digitized TIMESTAMP,
    timestamp_metadata TIMESTAMP,
    
    -- GPS metadata
    gps_latitude DOUBLE PRECISION,
    gps_longitude DOUBLE PRECISION,
    gps_altitude DOUBLE PRECISION,
    
    -- Camera metadata
    camera_make VARCHAR(255),
    camera_model VARCHAR(255),
    lens_model VARCHAR(255),
    
    -- Image dimensions
    width INTEGER,
    height INTEGER,
    orientation INTEGER,
    
    -- File metadata
    file_format VARCHAR(50),
    
    -- Extraction metadata
    extraction_method VARCHAR(50) DEFAULT 'exif',
    extraction_version VARCHAR(50),
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Raw EXIF data for debugging/audit (JSONB for flexibility)
    raw_exif JSONB
);

-- Add comment explaining the table
COMMENT ON TABLE photo_metadata IS 'Stores EXIF metadata from image files for Evidence Timeline Phase 1A';
COMMENT ON COLUMN photo_metadata.timestamp_original IS 'EXIF DateTimeOriginal - when photo was taken';
COMMENT ON COLUMN photo_metadata.gps_latitude IS 'GPS latitude in decimal degrees';
COMMENT ON COLUMN photo_metadata.gps_longitude IS 'GPS longitude in decimal degrees';
COMMENT ON COLUMN photo_metadata.camera_make IS 'Camera manufacturer (e.g., Apple, Canon, DJI)';
COMMENT ON COLUMN photo_metadata.camera_model IS 'Camera model (e.g., iPhone 15 Pro Max)';
COMMENT ON COLUMN photo_metadata.lens_model IS 'Lens model if available';
COMMENT ON COLUMN photo_metadata.orientation IS 'Image orientation: 1=normal, 3=rotated180, 6=rotated270, 8=rotated90';

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_photo_metadata_timestamp ON photo_metadata(timestamp_original);
CREATE INDEX IF NOT EXISTS idx_photo_metadata_gps ON photo_metadata(gps_latitude, gps_longitude) 
    WHERE gps_latitude IS NOT NULL AND gps_longitude IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_photo_metadata_camera ON photo_metadata(camera_make, camera_model)
    WHERE camera_make IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_photo_metadata_document ON photo_metadata(document_id);

-- Record migration
INSERT INTO schema_migrations (migration_name) VALUES ('003_photo_metadata.sql');
