-- Migration 012: Object Detection
-- Operation Object Detection - YOLOv8n integration
-- 
-- This migration adds support for storing object detection observations.
-- Each detection includes label, confidence, and bounding box coordinates.
--
-- Bounding boxes stored in both pixel and normalized coordinates for flexibility.

-- Create enum for detection source tracking
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'detection_source_enum') THEN
        CREATE TYPE detection_source_enum AS ENUM ('yolo', 'other');
    END IF;
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

-- Create object_detections table
-- This table stores individual object detection observations
CREATE TABLE IF NOT EXISTS object_detections (
    id SERIAL PRIMARY KEY,
    artifact_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Operation Plugin Foundation: Provenance fields
    plugin_name VARCHAR(255) NOT NULL,
    engine_name VARCHAR(255) NOT NULL,
    plugin_version VARCHAR(50),
    processed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    artifact_hash VARCHAR(64),
    
    -- Detection data
    label VARCHAR(255) NOT NULL,
    confidence DECIMAL(5, 4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    
    -- Bounding box in pixel coordinates
    bbox_x1 INTEGER NOT NULL,
    bbox_y1 INTEGER NOT NULL,
    bbox_x2 INTEGER NOT NULL,
    bbox_y2 INTEGER NOT NULL,
    
    -- Bounding box in normalized coordinates (0-1 range)
    bbox_norm_x1 DECIMAL(10, 6) CHECK (bbox_norm_x1 >= 0 AND bbox_norm_x1 <= 1),
    bbox_norm_y1 DECIMAL(10, 6) CHECK (bbox_norm_y1 >= 0 AND bbox_norm_y1 <= 1),
    bbox_norm_x2 DECIMAL(10, 6) CHECK (bbox_norm_x2 >= 0 AND bbox_norm_x2 <= 1),
    bbox_norm_y2 DECIMAL(10, 6) CHECK (bbox_norm_y2 >= 0 AND bbox_norm_y2 <= 1),
    
    -- Detection source
    source VARCHAR(50) DEFAULT 'yolo',
    
    -- Soft delete support
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT bbox_pixel_check CHECK (bbox_x2 >= bbox_x1 AND bbox_y2 >= bbox_y1),
    CONSTRAINT bbox_norm_check CHECK (
        bbox_norm_x2 IS NULL OR bbox_norm_x1 IS NULL OR bbox_norm_x2 >= bbox_norm_x1
    )
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_object_detections_artifact_id ON object_detections(artifact_id);
CREATE INDEX IF NOT EXISTS idx_object_detections_label ON object_detections(label);
CREATE INDEX IF NOT EXISTS idx_object_detections_confidence ON object_detections(confidence);
CREATE INDEX IF NOT EXISTS idx_object_detections_plugin_name ON object_detections(plugin_name);
CREATE INDEX IF NOT EXISTS idx_object_detections_engine_name ON object_detections(engine_name);
CREATE INDEX IF NOT EXISTS idx_object_detections_deleted_at ON object_detections(deleted_at);

-- Index for search by label (common query pattern)
CREATE INDEX IF NOT EXISTS idx_object_detections_label_artifact ON object_detections(label, artifact_id);

-- Insert migration record
INSERT INTO schema_migrations (migration_name)
VALUES ('012_object_detection.sql')
ON CONFLICT (migration_name) DO NOTHING;
