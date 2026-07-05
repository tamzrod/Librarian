# Object Detection Plugin Architecture

**Plugin:** Object Detection  
**Status:** 📋 Planned  
**Implementation:** Not Started

---

## Overview

The Object Detection plugin will follow the standard plugin architecture pattern. This document describes the planned architecture for implementing object detection using YOLOv8.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   Object Detection Architecture                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Scanner    │───▶│   Worker     │───▶│   Backend    │       │
│  │              │    │   Handler    │    │              │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                  │                   │                  │
│         │                  ▼                   │                  │
│         │           ┌──────────────┐          │                  │
│         │           │   YOLOv8    │          │                  │
│         │           │    Model    │          │                  │
│         │           └──────────────┘          │                  │
│         │                                     │                  │
│         ▼                                     ▼                  │
│  ┌──────────────┐                      ┌──────────────┐         │
│  │  documents   │                      │ detections   │         │
│  │    table     │                      │    table     │         │
│  └──────────────┘                      └──────────────┘         │
│                                                   │              │
│                                                   ▼              │
│                                          ┌──────────────┐        │
│                                          │     API      │        │
│                                          │   Routes     │        │
│                                          └──────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Worker Handler

**File:** `workers/object_detection_worker.py` (planned)

**Class:** `ObjectDetectionWorker`

**Responsibilities:**
- Validate image files
- Load and run model inference
- Post-process detections (NMS, filtering)
- Persist results to database
- Handle errors gracefully

**Job Type:** `object_detection`

```python
# Planned implementation
class ObjectDetectionWorker(BaseWorker):
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}
    
    def __init__(self, backend, model_path: str = "yolov8s.pt"):
        self.backend = backend
        self.model = YOLO(model_path)
    
    def process(self, job: dict) -> dict:
        # Load image, run inference, save detections
        ...
```

### 2. Detection Model

**Framework:** Ultralytics YOLOv8

**Model Options:**
- `yolov8n.pt` - Nano (fastest, lowest accuracy)
- `yolov8s.pt` - Small (balanced)
- `yolov8m.pt` - Medium (higher accuracy)
- `yolov8l.pt` - Large (high accuracy)
- `yolov8x.pt` - Extra-large (highest accuracy)

**Model Loading:**
```python
from ultralytics import YOLO

model = YOLO('yolov8s.pt')
results = model.predict('image.jpg', conf=0.25)
```

### 3. Post-Processing

**Non-Maximum Suppression (NMS):**
- Remove duplicate detections
- Keep highest confidence detection per object
- IoU threshold: 0.45

**Confidence Filtering:**
- Filter detections below threshold
- Default: 0.25

**Aggregation:**
- Count objects per class
- Generate presence flags
- Summary statistics

### 4. Storage Backend

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

### 5. API Routes

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
5. ObjectDetectionWorker processes job
         ↓
6. YOLOv8 model runs inference
         ↓
7. Post-processing (NMS, filtering)
         ↓
8. Detections saved to database
         ↓
9. API exposes to clients
```

---

## Dependencies

### Required

| Dependency | Version | Purpose |
|------------|---------|---------|
| ultralytics | >= 8.0 | YOLOv8 model and inference |
| torch | >= 2.0 | Deep learning framework |
| torchvision | >= 0.15 | Model utilities |
| Pillow | >= 9.0 | Image processing |
| psycopg2 | >= 2.9 | PostgreSQL database |

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
| `OBJECT_DETECTION_MODEL` | yolov8s | Model variant |
| `OBJECT_DETECTION_CONF` | 0.25 | Confidence threshold |
| `OBJECT_DETECTION_MAX_DET` | 100 | Maximum detections |

### Plugin Configuration

```yaml
# config/plugins.yaml
plugins:
  object_detection:
    enabled: false
    job_type: object_detection
    model: yolov8s
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