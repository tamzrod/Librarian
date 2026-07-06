# Plugin Development Guide

**Version**: 1.0  
**Last Updated**: 2026-07-05

---

## Overview

This guide documents how to create new plugins for Librarian. A plugin transforms artifacts into structured evidence through the processing pipeline.

## Artifact Tier Classification

Every plugin produces an artifact that falls into one of two tiers:

| Tier | Name | Characteristics | Recovery Required | Examples |
|------|------|-----------------|------------------|----------|
| **1A** | Derived Artifacts | Expensive to generate, may require GPU/models, recovery justified | Yes | embeddings, OCR, object detection |
| **1B** | Disposable Cache | Cheap to regenerate, no external dependencies | No | thumbnails, previews |

### Tier 1A Plugins (Derived Artifacts)

**When to use:**
- Plugin requires GPU or significant computation
- Plugin uses external APIs or models
- Plugin output is expensive to regenerate
- Losing the output is a cache miss (NOT corruption)

**Requirements:**
- Must provide recovery handler for the artifact
- Must implement integrity auditing
- Must document regeneration cost

### Tier 1B Plugins (Disposable Cache)

**When to use:**
- Plugin output is cheap to generate (<1 second CPU)
- Plugin has no external dependencies
- Plugin output is purely for UX (not evidence)
- Losing the output should trigger automatic regeneration

**Requirements:**
- NO recovery handler
- NO integrity auditing
- Must provide placeholder while regenerating
- Document that output is disposable cache

**Examples of Tier 1B:**
- Thumbnail generation (see [Thumbnail Contract](../../architecture/derived-artifact-contract.md#thumbnail-specific-contract))
- Preview image generation
- Resized image generation
- Filmstrip generation

## Plugin Anatomy

```
┌─────────────────────────────────────────────────────────────┐
│                      Plugin Components                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
│  │ Worker      │──►│ Handler     │──►│ Artifacts/  │      │
│  │ Registration│   │ Function    │   │ Metadata    │      │
│  └─────────────┘   └─────────────┘   └─────────────┘      │
│        │                                      │             │
│        ▼                                      ▼             │
│  ┌─────────────┐                       ┌─────────────┐      │
│  │ Plugin      │                       │ Database    │      │
│  │ Registry    │                       │ Tables      │      │
│  └─────────────┘                       └─────────────┘      │
│        │                                      │             │
│        ▼                                      ▼             │
│  ┌─────────────┐                       ┌─────────────┐      │
│  │ Settings    │                       │ Evidence    │      │
│  │ UI          │                       │ Graph       │      │
│  └─────────────┘                       └─────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Plugin Creation Lifecycle

### 1. Create Worker Implementation

The worker contains the processing logic.

**Location**: `workers/<plugin_name>_extractor.py`

**Template**:

```python
"""
<Plugin Name> Worker

Processes <artifact type> files for <purpose>.
"""

import logging
from typing import Optional

from .base import BaseWorker

logger = logging.getLogger(__name__)


class <PluginName>Extractor(BaseWorker):
    """
    Extract <something> from <artifact type> files.
    
    Example:
        extractor = <PluginName>Extractor(backend)
        results = extractor.process(document_id, artifact_path)
    """
    
    def __init__(self, backend, config: dict = None):
        super().__init__(backend)
        self.config = config or {}
        self._model = None
    
    def process(self, document_id: int, artifact_path: str) -> dict:
        """
        Process a document and extract <something>.
        
        Args:
            document_id: Database ID of the document
            artifact_path: Path to the artifact file
            
        Returns:
            Dict with extraction results and metadata
        """
        try:
            # Load model/data if needed
            model = self._load_model()
            
            # Process the artifact
            results = self._extract(artifact_path, model)
            
            # Store results
            self._save_results(document_id, results)
            
            return {
                'status': 'success',
                'document_id': document_id,
                'results': results,
            }
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}")
            return {
                'status': 'error',
                'document_id': document_id,
                'error': str(e),
            }
    
    def _load_model(self):
        """Load the ML model or data (lazy loading)."""
        if self._model is None:
            # Import here to avoid hard dependency
            from some_package import SomeModel
            
            model_path = self.config.get('model_path', 'default/model.pt')
            self._model = SomeModel(model_path)
        return self._model
    
    def _extract(self, artifact_path: str, model):
        """Extract <something> from the artifact."""
        # Implementation specific to the plugin
        pass
    
    def _save_results(self, document_id: int, results: dict):
        """Store results in the database."""
        # Implementation for persisting results
        pass
```

**Example**: `workers/object_detection_extractor.py`

---

### 2. Register Job Type

Register the handler with the worker system.

**Location**: `workers/worker.py`

**Steps**:

1. Import the extractor
2. Register the handler

```python
# In workers/worker.py

# Import the extractor
from workers.object_detection_extractor import ObjectDetectionExtractor

def run_worker():
    """Main worker entry point."""
    worker = Worker(backend)
    
    # ... other registrations ...
    
    # Register object detection handler
    def process_object_detection(document_id, artifact_path):
        extractor = ObjectDetectionExtractor(backend)
        return extractor.process(document_id, artifact_path)
    
    worker.register_handler('object_detection', process_object_detection)
    
    # ... rest of worker setup ...
```

**Job Type Naming**: Use `snake_case` consistent with existing patterns:
- `extract_photo_metadata`
- `generate_thumbnail`
- `object_detection`
- `run_ocr`

---

### 3. Define Plugin Manifest

Add the plugin to the registry definitions.

**Location**: `registry/plugin_registry.py`

**Steps**:

1. Add to `PLUGIN_DEFINITIONS`

```python
PLUGIN_DEFINITIONS = {
    # ... existing plugins ...
    
    '<plugin_name>': {
        'job_type': '<job_type_name>',
        'description': '<Human-readable description>',
        'category': '<category>',  # metadata, vision, audio, ai, etc.
        
        # Identity fields
        'namespace': '<namespace>',  # e.g., 'vision.yolo.ultralytics'
        'type': '<type>',            # e.g., 'object-detection'
        'engine': '<engine>',         # e.g., 'yolo'
        'version': '<version>',       # e.g., '1.0.0'
        
        # Dependencies (Operation Plugin Visibility Refactor)
        'required_packages': ['<package>'],  # e.g., ['ultralytics']
    },
}
```

2. Update `_discover_all_plugins()` if needed

The discovery function auto-detects from `required_packages`, but you may need to add custom logic for special detection.

---

### 4. Declare Dependencies

**Python Packages**: Add to `required_packages` in the manifest.

**If Not Installing Automatically**: Document installation in:

- Plugin documentation: `docs/plugins/<plugin-name>/README.md`
- Dependency guide: `docs/plugins/dependency-management.md`

**Installation Instructions Template**:

```markdown
## Installation

### Python Dependencies

```bash
pip install <package-name>
```

### System Dependencies (if required)

**Ubuntu/Debian**:
```bash
apt-get install <system-package>
```

**macOS**:
```bash
brew install <system-package>
```

### ML Models

Some plugins download models automatically on first use:

- `<model-name>` (~<size>MB): <purpose>
```

---

### 5. Define Settings Metadata

Configure how the plugin appears in Settings UI.

**Location**: `config/plugins.yaml`

```yaml
<plugin_name>:
  enabled: false  # Default to disabled for new plugins
  category: vision  # or metadata, audio, ai
  description: Detect objects in images using YOLOv8
  
  # Plugin-specific settings (future)
  settings:
    confidence_threshold: 0.5
    max_detections: 100
```

---

### 6. Add Database Migrations (If Required)

If the plugin needs new tables or columns.

**Location**: `storage/migrations/`

**Naming**: `013_<plugin_name>.sql` (next sequential number)

**Template**:

```sql
-- Migration: <Plugin Name>
-- Description: Add support for <plugin feature>
-- Created: 2026-07-05

-- Create main table
CREATE TABLE IF NOT EXISTS <table_name> (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Plugin-specific columns
    <column_name> <type>,
    
    -- Provenance
    plugin_version VARCHAR(20) DEFAULT '1.0.0',
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_document FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Create indexes
CREATE INDEX idx_<table_name>_document_id ON <table_name>(document_id);

-- Register migration
INSERT INTO schema_migrations (migration_name, applied_at)
VALUES ('013_<plugin_name>', CURRENT_TIMESTAMP);
```

**Apply Migrations**: Run the migration when the plugin is first enabled.

---

### 7. Add Backend Methods

Implement storage methods for the plugin results.

**Location**: `storage/postgres_backend.py`

**Template**:

```python
def save_<plugin>_results(self, document_id: int, results: dict) -> int:
    """
    Save <plugin> extraction results.
    
    Args:
        document_id: The document ID
        results: Dict with extraction results
        
    Returns:
        The ID of the inserted record
    """
    # SQL insert with parameterized queries
    query = """
        INSERT INTO <table_name> (document_id, <columns>)
        VALUES (%s, <values>)
        RETURNING id
    """
    
    with self.get_cursor() as cursor:
        cursor.execute(query, (document_id, ...))
        result = cursor.fetchone()
        return result[0]

def get_<plugin>_results(self, document_id: int) -> list[dict]:
    """
    Retrieve <plugin> results for a document.
    
    Args:
        document_id: The document ID
        
    Returns:
        List of result records
    """
    query = """
        SELECT * FROM <table_name>
        WHERE document_id = %s
    """
    
    with self.get_cursor() as cursor:
        cursor.execute(query, (document_id,))
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
```

---

### 8. Add API Support (If Needed)

If the plugin needs custom API endpoints.

**Location**: `api/routes/<feature>.py`

**Template**:

```python
"""
<Feature> API Routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/<feature>", tags=["<feature>"])


class <Feature>Response(BaseModel):
    """Response model for <feature>."""
    document_id: int
    results: list[dict]
    count: int


@router.get(
    "/documents/{document_id}/<feature>",
    response_model=<Feature>Response,
    summary="Get <feature> results"
)
async def get_<feature>(document_id: int):
    """
    Retrieve <feature> results for a document.
    """
    backend = get_backend()
    results = backend.get_<feature>_results(document_id)
    
    if results is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return <Feature>Response(
        document_id=document_id,
        results=results,
        count=len(results)
    )
```

---

### 9. Add UI Components (If Needed)

**Settings Page**: Update `dashboard/src/pages/Settings.tsx`

The plugin registry handles visibility automatically. No changes needed unless custom UI controls are required.

**Feature Pages**: Create or update in `dashboard/src/pages/`

```
dashboard/src/pages/<Feature>Page.tsx
```

---

### 10. Add Tests

**Unit Tests**: `tests/unit/test_<plugin>.py`

```python
"""
Unit tests for <Plugin> extractor.
"""

import pytest
from unittest.mock import Mock, patch

from workers.<plugin>_extractor import <Plugin>Extractor


class Test<Plugin>Extractor:
    """Tests for <Plugin>Extractor."""
    
    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        backend = Mock()
        return <Plugin>Extractor(backend)
    
    def test_process_valid_artifact(self, extractor, tmp_path):
        """Test processing a valid artifact."""
        # Create test file
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"fake image data")
        
        # Mock the model
        with patch.object(extractor, '_load_model') as mock_model:
            mock_model.return_value = Mock(
                predict=Mock(return_value={'objects': ['person', 'car']})
            )
            
            result = extractor.process(1, str(test_file))
        
        assert result['status'] == 'success'
        assert result['document_id'] == 1
    
    def test_process_invalid_artifact(self, extractor, tmp_path):
        """Test processing an invalid artifact."""
        test_file = tmp_path / "invalid.xyz"
        test_file.write_bytes(b"not an image")
        
        result = extractor.process(1, str(test_file))
        
        assert result['status'] == 'error'
        assert 'error' in result
```

**Integration Tests**: `tests/integration/test_<plugin>_integration.py`

```python
"""
Integration tests for <Plugin> with database.
"""

import pytest
from storage.postgres_backend import PostgresBackend


class Test<Plugin>Integration:
    """Integration tests with real database."""
    
    @pytest.fixture
    def backend(self):
        """Create backend instance."""
        return PostgresBackend()
    
    def test_save_and_retrieve(self, backend, sample_document):
        """Test saving and retrieving results."""
        # Save results
        results = {'objects': ['person'], 'confidence': 0.95}
        record_id = backend.save_<plugin>_results(sample_document.id, results)
        
        # Retrieve results
        retrieved = backend.get_<plugin>_results(sample_document.id)
        
        assert len(retrieved) == 1
        assert retrieved[0]['objects'] == ['person']
```

---

### 11. Add Documentation

**Plugin Directory**: `docs/plugins/<plugin-name>/`

```
docs/plugins/<plugin-name>/
├── README.md           # Overview
├── capabilities.md     # What it can do
├── metadata-schema.md  # Output format
├── architecture.md     # Technical details
└── roadmap.md         # Future improvements
```

**README Template**:

```markdown
# <Plugin Name>

**Status**: <Implemented|Beta|Design|Concept>  
**Plugin Version**: <version>  
**Engine**: <engine-name>

## Overview

<Description of what the plugin does>.

## Supported Inputs

| Format | Extensions |
|--------|------------|
| Images | jpg, jpeg, png, heic, webp, tiff |

## Example Output

```json
{
  "document_id": 123,
  "objects": [
    {"label": "person", "confidence": 0.95, "bbox": [x1, y1, x2, y2]},
    {"label": "car", "confidence": 0.87, "bbox": [x1, y1, x2, y2]}
  ],
  "count": 2,
  "processed_at": "2026-07-05T12:00:00Z"
}
```

## Installation

See [Dependency Management](../dependency-management.md) for requirements.

## Configuration

```yaml
plugins:
  <plugin_name>:
    enabled: true
    confidence_threshold: 0.5
    max_detections: 100
```

## Limitations

- <Known limitation 1>
- <Known limitation 2>

## Roadmap

- <Planned feature 1>
- <Planned feature 2>
```

---

## Complete Example: Object Detection Plugin

Here's the complete implementation of the Object Detection plugin:

### 1. Worker: `workers/object_detection_extractor.py`

```python
"""
Object Detection Worker

Detects objects in images using YOLOv8.
"""

import logging
from typing import Optional

from .base import BaseWorker

logger = logging.getLogger(__name__)


class ObjectDetectionExtractor(BaseWorker):
    """
    Detect objects in images using YOLOv8.
    """
    
    def __init__(self, backend, config: dict = None):
        super().__init__(backend)
        self.config = config or {}
        self._model = None
        self._confidence_threshold = self.config.get('confidence_threshold', 0.5)
        self._max_detections = self.config.get('max_detections', 100)
    
    def process(self, document_id: int, artifact_path: str) -> dict:
        """Process a document and detect objects."""
        try:
            model = self._load_model()
            results = self._detect_objects(artifact_path, model)
            self._save_detections(document_id, results)
            
            return {
                'status': 'success',
                'document_id': document_id,
                'objects': results,
                'count': len(results),
            }
        except Exception as e:
            logger.error(f"Object detection failed for {document_id}: {e}")
            return {
                'status': 'error',
                'document_id': document_id,
                'error': str(e),
            }
    
    def _load_model(self):
        """Lazy load YOLOv8 model."""
        if self._model is None:
            from ultralytics import YOLO
            self._model = YOLO('yolov8n.pt')
        return self._model
    
    def _detect_objects(self, artifact_path: str, model):
        """Run detection on artifact."""
        results = model(artifact_path, verbose=False)[0]
        detections = []
        
        for box in results.boxes:
            conf = float(box.conf[0])
            if conf < self._confidence_threshold:
                continue
            
            detections.append({
                'label': results.names[int(box.cls[0])],
                'confidence': conf,
                'bbox': box.xyxy[0].tolist(),
            })
        
        return detections[:self._max_detections]
    
    def _save_detections(self, document_id: int, detections: list):
        """Save detections to database."""
        self.backend.save_detections(document_id, detections)
```

### 2. Registration: `workers/worker.py`

```python
from workers.object_detection_extractor import ObjectDetectionExtractor

def run_worker():
    worker = Worker(backend)
    
    def process_object_detection(document_id, artifact_path):
        extractor = ObjectDetectionExtractor(backend)
        return extractor.process(document_id, artifact_path)
    
    worker.register_handler('object_detection', process_object_detection)
```

### 3. Manifest: `registry/plugin_registry.py`

```python
'object_detection': {
    'job_type': 'object_detection',
    'description': 'Detect objects in images',
    'category': 'vision',
    'namespace': 'vision.object-detection.yolo',
    'type': 'object-detection',
    'engine': 'yolo',
    'version': '1.0.0',
    'required_packages': ['ultralytics'],
},
```

### 4. Configuration: `config/plugins.yaml`

```yaml
object_detection:
  enabled: false
  category: vision
  description: Detect objects in images using YOLOv8n
```

### 5. Database Migration: `storage/migrations/012_object_detection.sql`

```sql
CREATE TABLE object_detections (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    label VARCHAR(100) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    bbox_x1 DECIMAL(10,2),
    bbox_y1 DECIMAL(10,2),
    bbox_x2 DECIMAL(10,2),
    bbox_y2 DECIMAL(10,2),
    plugin_version VARCHAR(20) DEFAULT '1.0.0',
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_object_detections_document_id ON object_detections(document_id);
```

---

## Checklist

Use this checklist when creating a new plugin:

- [ ] Create worker implementation
- [ ] Register handler in `worker.py`
- [ ] Add plugin definition to `PLUGIN_DEFINITIONS`
- [ ] Declare dependencies in manifest
- [ ] Add configuration template to `plugins.yaml`
- [ ] Create database migration (if needed)
- [ ] Implement backend storage methods
- [ ] Add API endpoints (if needed)
- [ ] Update Settings UI (automatic)
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Create documentation
- [ ] Update this guide with any new patterns

---

## Common Patterns

### Lazy Model Loading

```python
def _load_model(self):
    if self._model is None:
        from expensive_package import Model
        self._model = Model(self.config['model_path'])
    return self._model
```

### Batch Processing

```python
def process_batch(self, document_ids: list[int]) -> list[dict]:
    results = []
    for doc_id in document_ids:
        results.append(self.process(doc_id))
    return results
```

### Error Recovery

```python
def process(self, document_id, artifact_path):
    try:
        # Main processing
        return self._do_process(artifact_path)
    except SpecificError as e:
        # Handle specific error
        return {'status': 'error', 'error': str(e)}
    except Exception as e:
        # Log and re-raise for retry
        logger.exception(f"Unexpected error processing {document_id}")
        raise
```

### Progress Reporting

```python
def process(self, document_id, artifact_path):
    self.backend.update_job_status(
        document_id, 
        job_type=self.job_type,
        status='IN_PROGRESS'
    )
    
    try:
        results = self._do_process(artifact_path)
        self.backend.update_job_status(document_id, status='COMPLETED')
        return results
    except Exception:
        self.backend.update_job_status(document_id, status='FAILED')
        raise
```

---

*This guide provides the complete lifecycle for creating Librarian plugins.*

---

## Glossary

See [Architecture Glossary](../architecture/glossary.md) for definitions of key terms including artifact, cache miss, enrichment, and corruption.
