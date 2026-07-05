# Object Detection Plugin Metadata Schema

**Plugin:** Object Detection  
**Status:** 📋 Planned  
**Implementation:** Not Started

---

## Overview

The Object Detection plugin will generate structured metadata following this JSON schema. This schema defines the canonical output format for all object detection operations.

---

## JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ObjectDetection",
  "description": "Object detection metadata from images",
  "type": "object",
  "properties": {
    "plugin": {
      "type": "string",
      "const": "object-detection",
      "description": "Plugin identifier"
    },
    "version": {
      "type": "string",
      "const": "1.0",
      "description": "Schema version"
    },
    "document_id": {
      "type": "string",
      "format": "uuid",
      "description": "Document identifier in the system"
    },
    "model": {
      "type": "string",
      "description": "Detection model used (e.g., yolov8s)"
    },
    "processing_time_ms": {
      "type": "number",
      "description": "Time taken for inference in milliseconds"
    },
    "objects": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "label": {
            "type": "string",
            "description": "Object class name"
          },
          "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Detection confidence score"
          },
          "bbox": {
            "type": "array",
            "items": {
              "type": "number"
            },
            "minItems": 4,
            "maxItems": 4,
            "description": "Bounding box [x, y, width, height]"
          }
        },
        "required": ["label", "confidence", "bbox"]
      },
      "description": "Detected objects"
    },
    "summary": {
      "type": "object",
      "properties": {
        "total_objects": {
          "type": "integer",
          "description": "Total number of detected objects"
        },
        "object_counts": {
          "type": "object",
          "additionalProperties": {
            "type": "integer"
          },
          "description": "Count per object class"
        },
        "presence_flags": {
          "type": "object",
          "additionalProperties": {
            "type": "boolean"
          },
          "description": "Boolean flags for each class (has_person, has_dog, etc.)"
        }
      },
      "description": "Detection summary statistics"
    }
  },
  "required": ["plugin", "version", "document_id", "objects"]
}
```

---

## Example Output

### Full Output

```json
{
  "plugin": "object-detection",
  "version": "1.0",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "model": "yolov8s",
  "processing_time_ms": 245.5,
  "objects": [
    {
      "label": "person",
      "confidence": 0.94,
      "bbox": [100, 200, 75, 150]
    },
    {
      "label": "dog",
      "confidence": 0.87,
      "bbox": [450, 300, 120, 200]
    },
    {
      "label": "person",
      "confidence": 0.82,
      "bbox": [300, 150, 70, 140]
    },
    {
      "label": "car",
      "confidence": 0.76,
      "bbox": [50, 400, 300, 180]
    }
  ],
  "summary": {
    "total_objects": 4,
    "object_counts": {
      "person": 2,
      "dog": 1,
      "car": 1
    },
    "presence_flags": {
      "has_person": true,
      "has_dog": true,
      "has_car": true,
      "has_bicycle": false
    }
  }
}
```

### Minimal Output (no detections)

```json
{
  "plugin": "object-detection",
  "version": "1.0",
  "document_id": "660e8400-e29b-41d4-a716-446655440001",
  "model": "yolov8s",
  "processing_time_ms": 180.2,
  "objects": [],
  "summary": {
    "total_objects": 0,
    "object_counts": {},
    "presence_flags": {
      "has_person": false,
      "has_dog": false,
      "has_car": false
    }
  }
}
```

### Energy Infrastructure Example

```json
{
  "plugin": "object-detection",
  "version": "1.0",
  "document_id": "770e8400-e29b-41d4-a716-446655440002",
  "model": "yolov8s",
  "processing_time_ms": 312.8,
  "objects": [
    {
      "label": "solar_panel",
      "confidence": 0.91,
      "bbox": [50, 100, 400, 300]
    },
    {
      "label": "solar_panel",
      "confidence": 0.89,
      "bbox": [500, 100, 400, 300]
    },
    {
      "label": "transformer",
      "confidence": 0.78,
      "bbox": [900, 200, 80, 120]
    }
  ],
  "summary": {
    "total_objects": 3,
    "object_counts": {
      "solar_panel": 2,
      "transformer": 1
    },
    "presence_flags": {
      "has_solar_panel": true,
      "has_transformer": true,
      "has_inverter": false
    }
  }
}
```

---

## Database Storage

The metadata will be stored in the `detections` table:

```sql
-- Detections table
CREATE TABLE detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    label VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    bbox_x FLOAT NOT NULL,
    bbox_y FLOAT NOT NULL,
    bbox_width FLOAT NOT NULL,
    bbox_height FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Document detection summary
CREATE TABLE detection_summary (
    document_id UUID PRIMARY KEY REFERENCES documents(id),
    model VARCHAR(50),
    processing_time_ms FLOAT,
    total_objects INTEGER,
    object_counts JSONB,
    presence_flags JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_detections_document ON detections(document_id);
CREATE INDEX idx_detections_label ON detections(label);
CREATE INDEX idx_detections_confidence ON detections(confidence);
CREATE INDEX idx_detection_summary_total ON detection_summary(total_objects);
```

---

## Field Mapping

### Objects Table

| JSON Field | Database Column | Type |
|------------|-----------------|------|
| document_id | document_id | UUID |
| objects[].label | label | VARCHAR(100) |
| objects[].confidence | confidence | FLOAT |
| objects[].bbox[0] | bbox_x | FLOAT |
| objects[].bbox[1] | bbox_y | FLOAT |
| objects[].bbox[2] | bbox_width | FLOAT |
| objects[].bbox[3] | bbox_height | FLOAT |

### Detection Summary Table

| JSON Field | Database Column | Type |
|------------|-----------------|------|
| document_id | document_id | UUID |
| model | model | VARCHAR(50) |
| processing_time_ms | processing_time_ms | FLOAT |
| summary.total_objects | total_objects | INTEGER |
| summary.object_counts | object_counts | JSONB |
| summary.presence_flags | presence_flags | JSONB |

---

## Bounding Box Format

Bounding boxes follow the format `[x, y, width, height]`:

```
(x, y) ──────────────┐
│                     │
│    ┌───────────┐    │
│    │  Object   │    │
│    │           │    │
│    └───────────┘    │
│                     │
│                     │
└─────────────────────┘
       width
       
x: Top-left corner X coordinate
y: Top-left corner Y coordinate
width: Width of bounding box
height: Height of bounding box
```

Coordinates are in image pixels, starting from (0, 0) at the top-left corner.

---

## Object Class Reference

### Standard Classes

| Class | Category |
|-------|----------|
| person | People |
| bicycle | Vehicle |
| motorcycle | Vehicle |
| car | Vehicle |
| truck | Vehicle |
| bus | Vehicle |
| drone | Electronics |
| laptop | Electronics |
| phone | Electronics |
| dog | Animal |
| cat | Animal |
| bird | Animal |
| solar_panel | Energy |
| transformer | Energy |
| inverter | Energy |
| helmet | Safety |
| vest | Safety |
| goggles | Safety |
| gloves | Safety |

### Extended Classes (COCO)

The YOLOv8 model supports 80 COCO classes. See [datasets.md](./datasets.md) for the full list.