# Namespacing Strategy

**Purpose:** Document the naming conventions for plugins to avoid ambiguity

---

## Namespacing Requirements

Avoid ambiguous ownership:

```
BAD:
- gps
- text
- object

GOOD:
- exif.gps
- ocr.text
- yolo.object
- caption.text
```

## Namespace Structure

### Format

```
{category}.{type}.{engine}
```

### Components

| Component | Description | Examples |
|-----------|-------------|----------|
| `category` | High-level category | `metadata`, `vision`, `audio`, `text`, `embeddings` |
| `type` | Type of extraction | `exif`, `ocr`, `object-detection`, `transcription` |
| `engine` | Specific engine | `pillow`, `yolo`, `tesseract`, `whisper` |

## Category Namespaces

### metadata

Extraction of metadata from files.

```
metadata.exif.pillow           # EXIF extraction
metadata.exif.exiftool        # EXIF with exiftool
metadata.file-info             # Basic file information
```

### vision

Visual analysis of images/videos.

```
vision.object-detection.yolo   # YOLO object detection
vision.object-detection.dino   # Grounding DINO
vision.object-detection.owl     # OWL-ViT
vision.ocr.tesseract           # Tesseract OCR
vision.ocr.cloud-vision        # Google Cloud Vision
vision.captioning.blip        # BLIP image captioning
vision.captioning.gpt4v       # GPT-4V captioning
```

### audio

Audio analysis and transcription.

```
audio.transcription.whisper    # OpenAI Whisper
audio.transcription.assemblyai  # AssemblyAI
audio.analysis.pydub          # Audio analysis
```

### text

Text extraction and analysis.

```
text.extraction.markdown       # Markdown extraction
text.extraction.html           # HTML extraction
text.extraction.pdf            # PDF text extraction
```

### embeddings

Vector embeddings for similarity search.

```
embeddings.openai.ada002      # OpenAI ada-002
embeddings.sentence-transformers  # HuggingFace
embeddings.local.all-minilm   # Local all-MiniLM
```

## Current to Future Mapping

### Current Plugin Names

| Current | Proposed | Notes |
|---------|----------|-------|
| `photo_metadata` | `metadata.exif.pillow` | EXIF via PIL |
| `thumbnail` | `metadata.thumbnail.pillow` | Thumbnail via PIL |
| `ocr` | `vision.ocr.tesseract` | Tesseract OCR |
| `object_detection` | `vision.object-detection.yolo` | YOLO detection |
| `transcription` | `audio.transcription.whisper` | Whisper |
| `embeddings` | `embeddings.openai` | OpenAI embeddings |

## Migration Path

### Phase 1: Add Alias

Support both old and new names.

```python
# Alias mapping
PLUGIN_ALIASES = {
    'photo_metadata': 'metadata.exif.pillow',
    'thumbnail': 'metadata.thumbnail.pillow',
    'ocr': 'vision.ocr.tesseract',
    'object_detection': 'vision.object-detection.yolo',
    'transcription': 'audio.transcription.whisper',
    'embeddings': 'embeddings.openai',
}
```

### Phase 2: Update References

Update all internal references to use new names.

### Phase 3: Remove Aliases

Remove old names after deprecation period.

## Namespace Validation

```python
import re

# Valid namespace pattern
NAMESPACE_PATTERN = re.compile(
    r'^[a-z][a-z0-9]*'  # category
    r'\.[a-z][a-z0-9-]*'  # type
    r'\.[a-z][a-z0-9-]*$'  # engine
)

def validate_namespace(namespace: str) -> bool:
    """Validate plugin namespace format."""
    return bool(NAMESPACE_PATTERN.match(namespace))

# Examples
assert validate_namespace('metadata.exif.pillow')  # Valid
assert validate_namespace('vision.object-detection.yolo')  # Valid
assert validate_namespace('embeddings.openai.ada002')  # Valid
assert not validate_namespace('photo_metadata')  # Invalid - no namespace
assert not validate_namespace('yolo')  # Invalid - no type
```

## Namespace in Code

### Plugin Registry

```python
PLUGIN_DEFINITIONS = {
    'metadata.exif.pillow': {
        'job_type': 'extract_exif',
        'description': 'Extract EXIF metadata using PIL',
        'category': 'metadata',
        'type': 'exif',
        'engine': 'pillow',
        'version': '1.0.0',
    },
    'vision.object-detection.yolo': {
        'job_type': 'detect_objects',
        'description': 'Object detection using YOLOv8',
        'category': 'vision',
        'type': 'object-detection',
        'engine': 'yolo',
        'version': '1.0.0',
    },
}
```

### Job Types

```python
# Namespaced job types
JOB_TYPES = {
    'metadata.exif.pillow': 'extract_exif',
    'vision.object-detection.yolo': 'detect_objects',
    'vision.ocr.tesseract': 'run_ocr',
}
```

## Database Schema

### Plugin Names in Tables

```sql
-- Using namespaced plugin names
CREATE TABLE photo_metadata (
    document_id INTEGER REFERENCES documents(id),
    plugin_name VARCHAR(100) NOT NULL DEFAULT 'metadata.exif.pillow',
    engine_name VARCHAR(100) NOT NULL,
    ...
);
```

## Display Names

For UI display, use readable names:

```python
# Display name mapping
DISPLAY_NAMES = {
    'metadata.exif.pillow': 'EXIF Metadata (PIL)',
    'metadata.thumbnail.pillow': 'Thumbnail Generation',
    'vision.object-detection.yolo': 'Object Detection (YOLO)',
    'vision.ocr.tesseract': 'OCR (Tesseract)',
}

def get_display_name(plugin_name: str) -> str:
    """Get human-readable display name for plugin."""
    return DISPLAY_NAMES.get(plugin_name, plugin_name)
```

## Summary

| Aspect | Current | Proposed |
|--------|---------|----------|
| Namespace | ❌ None | ✅ `category.type.engine` |
| Example | `photo_metadata` | `metadata.exif.pillow` |
| Uniqueness | ❌ May conflict | ✅ Guaranteed |
| Extensibility | ❌ Limited | ✅ High |

---

## Implementation Checklist

- [ ] Define namespace format
- [ ] Update PLUGIN_DEFINITIONS with namespaces
- [ ] Add namespace validation
- [ ] Update job types
- [ ] Update database columns
- [ ] Update API responses
- [ ] Add display name mapping
