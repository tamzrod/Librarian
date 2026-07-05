# Object Detection Plugin

**Status:** 📋 Architecture Planned  
**Type:** Content Analysis Plugin  
**Implementation:** Not Started

---

## Overview

The Object Detection plugin extracts factual object information from images. It detects objects and reports: labels, confidence scores, and bounding boxes. The plugin does not interpret, reason, or assign meaning to detections.

**Philosophy:** Librarian only catalogs facts. Correlation and reasoning belong to humans, AI agents, search layers, and applications.

---

## Librarian Philosophy

### What Librarian Does

```
Image contains:
- object = car
- gps = Cebu

Librarian stores:
- object=car
- gps=Cebu
```

### What Librarian Does NOT Do

```
Librarian does NOT conclude:
"The car is in Cebu."
```

### Who Performs Reasoning?

- **Humans**: Interpret context and meaning
- **AI Agents**: Draw conclusions from facts
- **Search Layers**: Match queries to facts
- **Applications**: Display and use information

---

## Plugin Overlap is Intentional

Multiple plugins may analyze the same artifact. This is by design.

### Example: picture.jpg

| Plugin | Output |
|--------|--------|
| EXIF Plugin | GPS, Timestamp, Camera |
| Object Detection | person, car |
| Grounding DINO | transformer, inverter |
| OCR Plugin | "Danger High Voltage" |
| Caption Plugin | textual description |

**All outputs are stored independently.** No plugin is authoritative. Conflicting results are acceptable. Consumers decide how to use the information.

---

## Engine Abstraction

Object Detection is a plugin category. YOLO, Grounding DINO, OWL-ViT, etc. are engines.

```
Object Detection Plugin
    ├── YOLO
    ├── Grounding DINO
    ├── OWL-ViT
    ├── RT-DETR
    └── Future Engines
```

The rest of Librarian does not care which engine produced the metadata.

---

## Use Cases

1. **Content-Based Search**: Find images containing specific objects (e.g., "find all photos with dogs")
2. **Inventory Tracking**: Count objects in images (e.g., solar panels on rooftops)
3. **Safety Compliance**: Detect safety equipment (e.g., helmets, PPE)
4. **Media Analysis**: Analyze image content for organization

**Note:** Use cases are for consumers. Librarian only reports detected objects.

---

## What This Plugin Reports

For each detected object:

| Field | Type | Description |
|-------|------|-------------|
| label | string | Object class name |
| confidence | float | Detection confidence (0.0-1.0) |
| bbox | array | Bounding box [x, y, width, height] |

**No interpretation is included.** The plugin reports only what was detected.

---

## Artifacts

| Artifact | Description | Storage |
|----------|-------------|---------|
| detections | Object detection results | detections table |

**Note:** Annotated images are optional. Librarian focuses on metadata, not visualization.

---

## Searchable Metadata

The following metadata fields are indexed for search:

| Field | Type | Example | Searchable |
|-------|------|---------|------------|
| objects | array | ["person", "dog", "car"] | ✅ |
| object_count | int | 5 | ✅ |
| person_count | int | 2 | ✅ |
| vehicle_count | int | 1 | ✅ |
| has_<object> | bool | true | ✅ |

---

## Configuration

```yaml
# config/plugins.yaml
plugins:
  object_detection:
    enabled: false  # Not implemented yet
    job_type: object_detection
    engine: yolo-v8n
    confidence_threshold: 0.25
    max_detections: 100
```

---

## Related Documentation

- [Plugin Contract](./plugin-contract.md) - Integration requirements
- [Engines](./engines.md) - Supported detection engines
- [Capabilities](./capabilities.md) - Detailed capabilities
- [Architecture](./architecture.md) - Technical architecture
- [Metadata Schema](./metadata-schema.md) - Output schema
- [Roadmap](./roadmap.md) - Future improvements