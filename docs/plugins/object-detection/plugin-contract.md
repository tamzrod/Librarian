# Object Detection Plugin Contract

**Plugin:** Object Detection  
**Status:** 📋 Architecture Planning  
**Purpose:** Document the contract between the plugin and Librarian's core systems

---

## Overview

This document defines the contract that the Object Detection plugin must fulfill to integrate with Librarian. It describes inputs, outputs, lifecycle, error handling, and integration points.

**Philosophy:** Plugins are independent extractors. They report facts, not interpretations. Librarian stores facts. Consumers (humans, AI agents, applications) perform reasoning.

---

## Contract Boundaries

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Librarian Core                                │
│                                                                      │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐   │
│  │  Scanner    │────▶│   Job       │────▶│   Result            │   │
│  │             │     │  Scheduler  │     │   Storage           │   │
│  └─────────────┘     └─────────────┘     └─────────────────────┘   │
│         │                   │                      │                │
└─────────┼───────────────────┼──────────────────────┼────────────────┘
          │                   │                      │
          ▼                   ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Object Detection Plugin                            │
│                                                                      │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐   │
│  │   Worker    │────▶│   Engine    │────▶│   Metadata          │   │
│  │  Handler    │     │  Interface  │     │   Generator         │   │
│  └─────────────┘     └─────────────┘     └─────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Input Contract

### Supported Inputs

The plugin accepts the following input types:

| Type | Extensions | Notes |
|------|------------|-------|
| JPEG | .jpg, .jpeg | Primary format |
| HEIC | .heic, .heif | Apple format |
| PNG | .png | Lossless format |
| WebP | .webp | Modern format |

### Input Validation

The plugin **must** validate inputs:

1. **File exists**: Path must resolve to an existing file
2. **File readable**: File must have read permissions
3. **Format supported**: Extension must match supported types
4. **Image valid**: File must be parseable as an image

### Invalid Input Handling

| Condition | Behavior |
|-----------|----------|
| File not found | Skip job, log warning |
| Unsupported format | Skip job, log info |
| Corrupt image | Fail job, log error |
| Permission denied | Fail job, log error |

---

## Output Contract

### Metadata Schema

All plugin output **must** conform to the standard schema:

```json
{
  "plugin": "object-detection",
  "engine": "<engine-identifier>",
  "document_id": "<uuid>",
  "objects": [
    {
      "label": "string",
      "confidence": 0.0-1.0,
      "bbox": [x, y, width, height]
    }
  ],
  "summary": {
    "total_objects": 0,
    "object_counts": {},
    "presence_flags": {}
  }
}
```

### Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| plugin | string | ✅ | Must be "object-detection" |
| engine | string | ✅ | Engine identifier (e.g., "yolo-v8n") |
| document_id | string | ✅ | Librarian document UUID |
| objects | array | ✅ | Array of detection objects |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| version | string | Schema version (default: "1.0") |
| processing_time_ms | number | Inference time in milliseconds |
| summary | object | Aggregated statistics |

### Object Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| label | string | ✅ | Object class name |
| confidence | number | ✅ | Confidence score (0.0-1.0) |
| bbox | array | ✅ | [x, y, width, height] |

---

## Lifecycle Contract

### Job Execution

```
1. Scheduler queues job with type "object_detection"
         ↓
2. Worker picks up job
         ↓
3. Worker validates input file
         ↓
4. Worker loads detection engine
         ↓
5. Worker runs inference
         ↓
6. Worker generates metadata
         ↓
7. Worker stores results
         ↓
8. Worker marks job complete
```

### Job States

| State | Description |
|-------|-------------|
| queued | Job created, waiting for worker |
| running | Worker processing job |
| completed | Successfully processed |
| failed | Processing failed |

### Error Handling

| Error Type | Handling Strategy |
|------------|-------------------|
| Invalid input | Skip (no retry) |
| Engine load failure | Retry 3x, then fail |
| Inference failure | Retry 3x, then fail |
| Storage failure | Retry 3x, then fail |

---

## Integration Points

### Configuration

The plugin reads configuration from `config/plugins.yaml`:

```yaml
plugins:
  object_detection:
    enabled: true
    engine: yolo-v8n
    confidence_threshold: 0.25
    max_detections: 100
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| OBJECT_DETECTION_ENABLED | false | Enable/disable plugin |
| OBJECT_DETECTION_ENGINE | yolo-v8n | Engine to use |
| OBJECT_DETECTION_CONF | 0.25 | Confidence threshold |

### Registry Integration

The plugin **must** register with the plugin registry:

```python
from registry.plugin_registry import PluginRegistry

registry = PluginRegistry()
registry.register(
    name="object-detection",
    job_type="object_detection",
    handler=ObjectDetectionWorker,
    supported_types={".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
)
```

### Database Storage

The plugin stores results in the `detections` table:

```sql
CREATE TABLE detections (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    engine VARCHAR(50),
    label VARCHAR(100),
    confidence FLOAT,
    bbox_x FLOAT,
    bbox_y FLOAT,
    bbox_width FLOAT,
    bbox_height FLOAT,
    created_at TIMESTAMP
);
```

---

## Independence Contract

### Plugin Isolation

Each plugin is independent:

1. **No cross-plugin dependencies**: Object detection does not depend on EXIF
2. **Parallel execution**: Plugins run independently
3. **No state sharing**: Plugins maintain no state between runs

### Overlap is Intentional

Multiple plugins may analyze the same artifact:

```
picture.jpg

EXIF Plugin → GPS, Timestamp, Camera
Object Detection → person, car, dog
OCR Plugin → "DANGER" text
Caption Plugin → "street scene with vehicles"
```

**All outputs are stored independently.** Librarian does not resolve conflicts.

### Fact-Only Output

The plugin **must not**:
- Assign meaning to detections
- Draw conclusions from detections
- Correlate detections with other metadata
- Make recommendations based on detections

The plugin **must**:
- Report what was detected
- Report confidence scores
- Report bounding boxes (if available)

---

## Performance Contract

### Resource Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| Memory per image | 2GB | Max memory for inference |
| Processing time | 60s | Max time per image |
| Max detections | 100 | Max objects per image |

### Target Performance

| Metric | Target | Engine |
|--------|--------|--------|
| Latency (CPU) | < 500ms | YOLOv8s |
| Latency (CPU) | < 100ms | YOLOv8n |
| Latency (GPU) | < 20ms | YOLOv8s |

---

## Versioning Contract

### Schema Versioning

The output schema follows semantic versioning:

- **Major version**: Breaking changes to structure
- **Minor version**: Additive changes (new fields)
- **Patch version**: Bug fixes

Current version: `1.0`

### Engine Versioning

Each engine should report its version:

```json
{
  "engine": "yolo-v8n",
  "engine_version": "8.0.0"
}
```

---

## Testing Contract

### Unit Tests

Plugins must provide unit tests for:

- Input validation
- Output schema generation
- Error handling paths

### Integration Tests

Plugins must pass integration tests for:

- Worker handler execution
- Database persistence
- Registry integration

### Contract Tests

The plugin contract is verified by:

```bash
python -m pytest tests/test_object_detection_contract.py -v
```

---

## Compliance Checklist

A compliant Object Detection plugin:

- [ ] Accepts supported image formats
- [ ] Validates all inputs
- [ ] Produces conforming metadata
- [ ] Registers with plugin registry
- [ ] Handles errors gracefully
- [ ] Reports facts only (no interpretations)
- [ ] Stores results in detections table
- [ ] Follows resource limits
- [ ] Provides unit tests
- [ ] Provides integration tests

---

## Related Documentation

- [Object Detection README](./README.md)
- [Object Detection Architecture](./architecture.md)
- [Object Detection Metadata Schema](./metadata-schema.md)
- [Object Detection Engines](./engines.md)
- [Plugin Registry Implementation](../../refactor/P13-P15-plugin-architecture.md)
