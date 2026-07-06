# Plugin Contract

This document defines the required declarations that every Librarian plugin must provide. These declarations establish the plugin's dependencies, artifact outputs, and database requirements.

## Required Declarations

Every plugin must declare the following sections:

```yaml
plugin: <plugin_name>
dependencies:
  - <package_name>
cache:
  - <cache_type>
artifact_outputs:
  - <artifact_name>
database_tables:
  - <table_name>
```

---

## Declaration Reference

### plugin

**Required:** Yes

**Format:** String identifier for the plugin.

**Rules:**
- Must be unique across all plugins
- Must match the directory name in `plugins/`
- Must be lowercase with hyphens allowed

### dependencies

**Required:** Yes

**Format:** List of Python package names or model files.

**Examples:**
- `ultralytics` — Python package from PyPI
- `yolov8n.pt` — Model file from HuggingFace or local cache

**Rules:**
- All packages must be installable via pip
- All model files must be downloadable or pre-bundled
- Dependencies must be declared in `requirements.txt` or `setup.py`

### cache

**Required:** No (but recommended)

**Format:** List of cache type identifiers.

**Known cache types:**
- `torch` — PyTorch model cache
- `huggingface` — HuggingFace model cache
- `transformers` — Transformers library cache
- `pip` — pip package cache
- `plugin` — Plugin-specific cache directory

**Rules:**
- Cache directories can be safely deleted
- Cache will be regenerated on first use
- Cache paths must be in `/librarian-data/cache/` or plugin-specific locations

### artifact_outputs

**Required:** Yes

**Format:** List of artifact type identifiers.

**Known artifact types:**
- `thumbnails` — Preview images
- `embeddings` — Vector representations
- `ocr_output` — Extracted text
- `object_detection_results` — Bounding boxes and labels
- `transcriptions` — Audio/video transcriptions
- `entity_extraction` — Named entity results
- `event_extraction` — Event detection results
- `location_extraction` — Location data

**Rules:**
- Artifacts are Tier 1 (regeneratable)
- Missing artifacts are valid runtime state
- Database references to artifacts must be nullable

### database_tables

**Required:** Conditional

**Format:** List of table names.

**Rules:**
- Required only if plugin creates database tables
- Table names must follow naming conventions: `<plugin>_<entity>`
- Tables must be created via migrations, not in plugin code

---

## Example Plugin Declarations

### Object Detection Plugin

```yaml
plugin: object_detection

dependencies:
  - ultralytics
  - yolov8n.pt
  - torch

cache:
  - torch
  - huggingface

artifact_outputs:
  - object_detection_results

database_tables:
  - object_detection_results
```

### OCR Plugin

```yaml
plugin: ocr

dependencies:
  - pytesseract
  - Pillow
  - pdf2image

cache:
  - tesseract

artifact_outputs:
  - ocr_output

database_tables:
  - ocr_results
```

### Embedding Plugin

```yaml
plugin: embedding

dependencies:
  - sentence-transformers
  - torch

cache:
  - huggingface
  - transformers

artifact_outputs:
  - embeddings

database_tables:
  - document_embeddings
```

### EXIF Metadata Plugin

```yaml
plugin: exif

dependencies:
  - exif
  - Pillow

cache: []

artifact_outputs:
  - exif_metadata

database_tables:
  - photo_metadata
```

---

## Plugin Declaration Schema (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["plugin", "dependencies", "artifact_outputs"],
  "properties": {
    "plugin": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9-]*$"
    },
    "dependencies": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "cache": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["torch", "huggingface", "transformers", "pip", "plugin"]
      }
    },
    "artifact_outputs": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "database_tables": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

---

## Tier Mapping

| Declaration | Tier | Preservation Policy |
|-------------|------|---------------------|
| `dependencies` | 2 - Infrastructure | Keep on rebuild, keep on reset, delete on nuclear |
| `cache` | 2 - Infrastructure | Keep on rebuild, keep on reset, delete on nuclear |
| `artifact_outputs` | 1 - Derived Artifacts | Keep on rebuild, delete on reset, delete on nuclear |
| `database_tables` | 0 - Evidence | Keep on rebuild, delete on reset, delete on nuclear |

---

## Implementation Checklist

For plugin developers:

- [ ] Declare plugin name following naming conventions
- [ ] List all Python dependencies
- [ ] List all model file dependencies
- [ ] Declare required cache types
- [ ] Declare all artifact outputs
- [ ] Declare all database tables (if any)
- [ ] Ensure database tables are nullable references
- [ ] Handle missing artifacts gracefully in plugin code
- [ ] Document regeneration behavior

---

## Anti-Patterns

### Missing Declaration

```yaml
# WRONG: Missing required fields
plugin: object_detection
dependencies:
  - ultralytics
```

```yaml
# CORRECT: Complete declaration
plugin: object_detection
dependencies:
  - ultralytics
  - yolov8n.pt
artifact_outputs:
  - object_detection_results
```

### Non-Nullable Database References

```python
# WRONG: Assumes artifact always exists
thumbnail = Document.thumbnail_path  # Can be None!

# CORRECT: Handles missing artifacts
thumbnail = doc.thumbnail_path
if thumbnail and Path(thumbnail).exists():
    return load_thumbnail(thumbnail)
else:
    return Placeholder()
```

### Hardcoded Cache Paths

```python
# WRONG: Hardcoded path
cache_dir = "/root/.cache/huggingface"

# CORRECT: Use configuration
cache_dir = config.get("cache.huggingface", "/librarian-data/cache/huggingface")
```