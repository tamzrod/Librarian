# Object Detection Plugin Capabilities

**Plugin:** Object Detection  
**Status:** 📋 Architecture Documented  
**Implementation:** Not Started

---

## Overview

This document details the planned capabilities for the Object Detection plugin. The plugin reports factual detections only—no interpretations, conclusions, or correlations are made.

**Philosophy:** Librarian catalogs facts. Interpretation belongs to consumers (humans, AI agents, applications).

---

## Supported Object Classes

**Note:** Supported classes depend on the detection engine. See [engines.md](./engines.md) for details.

### YOLOv8 (Fixed Classes)

Standard COCO dataset classes:

| Category | Classes |
|----------|---------|
| People | person |
| Vehicles | bicycle, motorcycle, car, truck, bus |
| Animals | dog, cat, bird |
| Electronics | drone, laptop, phone |
| Common | chair, couch, potted plant, dining table, tv |

Full list: 80 COCO classes

### Open-Vocabulary Engines

Engines like Grounding DINO and OWL-ViT can detect arbitrary classes based on text prompts:

| Engine | Class Flexibility |
|--------|-----------------|
| Grounding DINO | Any text-described class |
| OWL-ViT | Any text-described class |

### Energy Infrastructure (Example)

These may require custom-trained models or open-vocabulary engines:

| Class | Category | Detection Approach |
|-------|----------|-------------------|
| solar_panel | Energy | Fine-tuned model or text prompt |
| transformer | Energy | Fine-tuned model or text prompt |
| inverter | Energy | Fine-tuned model or text prompt |

### Safety Equipment (Example)

| Class | Category | Detection Approach |
|-------|----------|-------------------|
| helmet | Safety | COCO (if trained) or custom |
| vest | Safety | Custom model or text prompt |

See [datasets.md](./datasets.md) for training information.

---

## Input Formats

| Format | Extension | Support Level |
|--------|-----------|---------------|
| JPEG | .jpg, .jpeg | ✅ Primary |
| HEIC | .heic, .heif | ✅ Supported |
| PNG | .png | ✅ Supported |
| WebP | .webp | ✅ Supported |

---

## Detection Parameters

### Confidence Threshold

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| confidence | 0.25 | 0.0-1.0 | Minimum confidence to report detection |

Lower values = more detections (including false positives)  
Higher values = fewer detections (higher precision)

### Non-Maximum Suppression (NMS)

| Parameter | Default | Description |
|-----------|---------|-------------|
| iou_threshold | 0.45 | IoU threshold for NMS |

### Detection Limits

| Parameter | Default | Maximum | Description |
|-----------|---------|---------|-------------|
| max_detections | 100 | 300 | Maximum objects per image |

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Latency (YOLOv8s) | < 500ms | Per image on CPU |
| Latency (YOLOv8n) | < 100ms | Per image on CPU |
| Memory Usage | < 2GB | Model + inference |
| Throughput (GPU) | 50 img/s | YOLOv8s on RTX 3080 |

---

## Output Capabilities

### Structured Metadata

Each detection includes:
- **label**: Object class name
- **confidence**: Detection confidence score
- **bbox**: Bounding box coordinates

### Aggregated Counts

Summary statistics:
- Total object count
- Count per class
- Presence flags (has_person, has_dog, etc.)

### Visualization

Optional annotated images with:
- Bounding boxes drawn on image
- Class labels
- Confidence scores

---

## Limitations

### Technical Limitations

1. **No Tracking**: Objects are not tracked across frames (video)
2. **No Segmentation**: Only bounding boxes, not pixel-level masks
3. **No 3D Pose**: No pose estimation or depth estimation
4. **No OCR**: Text in images is not detected

### Model Limitations

1. **Fixed Classes**: Cannot detect objects outside training set
2. **Domain Shift**: Performance may degrade on novel domains
3. **Occlusion**: Partially occluded objects may be missed
4. **Small Objects**: Very small objects (< 32px) difficult to detect

### Privacy Considerations

1. **Face Blur**: Faces in detected bounding boxes should be blur-reased
2. **License Plates**: Vehicle license plates should be masked
3. **No Biometrics**: Cannot be used for face recognition

---

## Future Capabilities

### Phase 2 Features

| Feature | Description | Priority |
|---------|-------------|----------|
| Instance Segmentation | Detect exact object boundaries | High |
| Video Processing | Process video frames | High |
| Object Tracking | Track objects across frames | Medium |
| Custom Classes | User-defined object classes | Medium |

### Phase 3 Features

| Feature | Description | Priority |
|---------|-------------|----------|
| Face Detection | Detect faces (separate from recognition) | Medium |
| Text Detection | OCR on detected text regions | Medium |
| Scene Classification | Classify overall scene type | Low |
| Image Captioning | Generate natural language descriptions | Low |

---

## Testing Requirements

### Unit Tests

- Model inference on sample images
- Confidence threshold filtering
- NMS implementation
- Output format validation

### Integration Tests

- Worker handler integration
- Database persistence
- API endpoint validation

### Performance Tests

- Latency benchmarks
- Memory usage profiling
- Batch processing throughput