# Object Detection Plugin Architecture

**Plugin:** Object Detection  
**Status:** 📋 Architecture Planned  
**Implementation:** Not Started

---

## Overview

The Object Detection plugin follows the standard plugin architecture pattern with support for multiple detection engines. This document describes the architecture that enables engine abstraction while maintaining Librarian's fact-only philosophy.

**Key Principle:** The plugin reports facts (detected objects) without interpretation. Correlation and reasoning are performed by consumers (humans, AI agents, applications).

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Object Detection Architecture                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   Scanner    │───▶│   Worker     │───▶│   Backend    │          │
│  │              │    │   Handler    │    │              │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│         │                  │                   │                     │
│         │                  │                   │                     │
│         │                  ▼                   │                     │
│         │         ┌─────────────────┐         │                     │
│         │         │ Engine Interface │         │                     │
│         │         └─────────────────┘         │                     │
│         │         ┌──────┬──────┬──────┐     │                     │
│         │         │      │      │      │     │                     │
│         │         ▼      ▼      ▼      ▼     │                     │
│         │     ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐│                     │
│         │     │YOLO │ │DINO │ │ OWL │ │RT-  ││                     │
│         │     │ v8  │ │     │ │ ViT │ │DETR ││                     │
│         │     └─────┘ └─────┘ └─────┘ └─────┘│                     │
│         │                                     │                     │
│         ▼                                     ▼                     │
│  ┌──────────────┐                      ┌──────────────┐            │
│  │  documents   │                      │ detections   │            │
│  │    table     │                      │    table     │            │
│  └──────────────┘                      └──────────────┘            │
│                                                    │                 │
│                                                    ▼                 │
│                                           ┌──────────────┐           │
│                                           │     API      │           │
│                                           │   Routes     │           │
│                                           └──────────────┘           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Worker Handler

**File:** `workers/object_detection_worker.py` (planned)

**Class:** `ObjectDetectionWorker`

**Responsibilities:**
- Validate image files
- Load detection engine (based on configuration)
- Run inference through engine interface
- Post-process detections (NMS, filtering)
- Persist results to database
- Handle errors gracefully

**Job Type:** `object_detection`

```python
# Planned implementation
class ObjectDetectionWorker(BaseWorker):
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}
    
    def __init__(self, backend, config: dict):
        self.backend = backend
        self.engine = self._load_engine(config.get('engine', 'yolo-v8n'))
        self.confidence_threshold = config.get('confidence_threshold', 0.25)
    
    def process(self, job: dict) -> dict:
        # Load image, run inference via engine, save detections
        ...
```

### 2. Engine Interface (Abstraction Layer)

**Purpose:** Enable multiple detection engines through a common interface

```python
# Engine interface (abstract base)
class DetectionEngine(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Engine identifier (e.g., 'yolo-v8n')"""
        
    @property
    @abstractmethod
    def supported_classes(self) -> List[str]:
        """Classes this engine can detect"""
        
    @abstractmethod
    def detect(self, image_path: str, conf_threshold: float) -> List[Detection]:
        """Run detection on image"""
```

### 3. Supported Engines

| Engine | Type | Classes | Strength |
|--------|------|---------|----------|
| YOLOv8 | Anchor-based CNN | 80 COCO | Speed |
| Grounding DINO | Transformer | Open-vocabulary | Flexibility |
| OWL-ViT | Vision Transformer | Open-vocabulary | HuggingFace integration |
| RT-DETR | Transformer | 80 COCO | Speed + Accuracy balance |

See [engines.md](./engines.md) for detailed engine documentation.

### 4. Post-Processing

**Non-Maximum Suppression (NMS):**
- Remove duplicate detections
- Keep highest confidence detection per object
- IoU threshold: 0.45

**Confidence Filtering:**
- Filter detections below configured threshold
- Default: 0.25

**Aggregation:**
- Count objects per class
- Generate presence flags
- Summary statistics

### 5. Storage Backend

**File:** `storage/postgres_backend.py` (planned updates)

**Methods:**
- `save_detections(document_id, detections)` - Persist detection results
- `get_detections(document_id)` - Retrieve detections

**Database Schema:**
```sql
-- Detections table
CREATE TABLE detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    engine VARCHAR(50),
    label VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    bbox_x FLOAT NOT NULL,
    bbox_y FLOAT NOT NULL,
    bbox_width FLOAT NOT NULL,
    bbox_height FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_detections_document ON detections(document_id);
CREATE INDEX idx_detections_label ON detections(label);
```

### 6. API Routes

**File:** `api/routes/detections.py` (planned)

**Endpoints:**
- `GET /detections/{document_id}` - Get detections for document
- `GET /detections/search?objects=person,dog` - Search by objects
- `GET /detections/stats` - Get detection statistics

---

## Data Flow

```
1. Image uploaded/scanned
         ↓
2. Collection watcher detects image
         ↓
3. Scanner creates document record
         ↓
4. Scheduler queues object_detection job
         ↓
5. ObjectDetectionWorker picks up job
         ↓
6. Worker loads configured detection engine
         ↓
7. Engine runs inference (any: YOLO, DINO, OWL-ViT, RT-DETR)
         ↓
8. Worker normalizes output to standard format
         ↓
9. Post-processing (NMS, filtering)
         ↓
10. Detections saved to database
         ↓
11. API exposes to clients
```

**Note:** Steps 6-8 enable engine abstraction. The output format is the same regardless of which engine is used.

---

## Dependencies

**Note:** Dependencies depend on which engine is selected. See [engines.md](./engines.md) for engine-specific requirements.

### Common Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Pillow | >= 9.0 | Image processing |
| psycopg2 | >= 2.9 | PostgreSQL database |
| numpy | >= 1.20 | Numerical operations |

### Engine-Specific Dependencies

| Engine | Dependencies |
|--------|--------------|
| YOLOv8 | ultralytics, torch, torchvision |
| Grounding DINO | transformers, torch |
| OWL-ViT | transformers, torch |
| RT-DETR | transformers, torch |

### Optional (GPU Acceleration)

| Dependency | Purpose |
|------------|---------|
| nvidia-cuda-toolkit | GPU support |
| cudnn | Deep learning acceleration |

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OBJECT_DETECTION_ENABLED` | false | Enable/disable plugin |
| `OBJECT_DETECTION_ENGINE` | yolo-v8n | Engine to use |
| `OBJECT_DETECTION_CONF` | 0.25 | Confidence threshold |
| `OBJECT_DETECTION_MAX_DET` | 100 | Maximum detections |

### Plugin Configuration

```yaml
# config/plugins.yaml
plugins:
  object_detection:
    enabled: false
    job_type: object_detection
    engine: yolo-v8n  # or grounding-dino, owl-vit, rt-detr
    confidence_threshold: 0.25
    max_detections: 100
```

---

## Error Handling

| Error | Handling |
|-------|----------|
| Unsupported format | Skip job, log warning |
| Model load failure | Retry 3x, then fail |
| Inference failure | Skip image, log error |
| Database error | Retry 3x, then fail |
| Memory exceeded | Reduce batch size |

---

## Performance Optimization

### CPU Inference

```python
# Use smaller model for CPU
model = YOLO('yolov8n.pt')  # ~6MB, fastest

# Reduce image size
results = model.predict('image.jpg', imgsz=640)
```

### GPU Inference

```python
# Use larger model with GPU
model = YOLO('yolov8s.pt')

# Enable GPU acceleration
results = model.predict('image.jpg', device='cuda')
```

### Batch Processing

```python
# Process multiple images
results = model.predict(['img1.jpg', 'img2.jpg', 'img3.jpg'])
```

---

## Security Considerations

1. **Model Security**: Validate model file integrity
2. **Input Validation**: Sanitize image paths
3. **Resource Limits**: Memory and time limits per job
4. **No External Access**: Model runs locally only

---

## Future Enhancements

1. **Custom Models**: Support for fine-tuned models
2. **Instance Segmentation**: Pixel-level detection
3. **Video Processing**: Frame-by-frame detection
4. **Object Tracking**: Track across video frames