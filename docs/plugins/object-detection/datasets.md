# Object Detection Plugin Datasets

**Plugin:** Object Detection  
**Status:** 📋 Planned  
**Implementation:** Not Started

---

## Overview

This document describes the candidate datasets for training and evaluating the Object Detection plugin.

---

## Candidate Datasets

### COCO (Common Objects in Context)

**Website:** https://cocodataset.org/  
**License:** Creative Commons Attribution 4.0

**Dataset Details:**
| Property | Value |
|----------|-------|
| Images | 330K |
| Categories | 80 |
| Annotations | 1.5M |
| Train/Val/Test Split | 118K/5K/41K |

**Use Case:** Primary dataset for general object detection.

**COCO Classes (80 total):**
```
person, bicycle, car, motorcycle, airplane, bus, train, truck, boat,
traffic light, fire hydrant, stop sign, parking meter, bench, bird,
cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe, backpack,
umbrella, handbag, tie, suitcase, frisbee, skis, snowboard, sports ball,
kite, baseball bat, baseball glove, skateboard, surfboard, tennis racket,
bottle, wine glass, cup, fork, knife, spoon, bowl, banana, apple, sandwich,
orange, broccoli, carrot, hot dog, pizza, donut, cake, chair, couch,
potted plant, bed, dining table, toilet, tv, laptop, mouse, remote,
keyboard, cell phone, microwave, oven, toaster, sink, refrigerator, book,
clock, vase, scissors, teddy bear, hair drier, toothbrush
```

---

### Open Images

**Website:** https://storage.googleapis.com/openimages/web/index.html  
**License:** Creative Commons Attribution 4.0

**Dataset Details:**
| Property | Value |
|----------|-------|
| Images | 1.9M |
| Categories | 600 |
| Annotations | 16M |
| Train/Val/Test Split | 1.7M/36K/125K |

**Use Case:** Extended object classes, larger scale.

**Advantages:**
- More categories (600 vs 80)
- Larger dataset
- Hierarchical category structure

**Considerations:**
- Larger download size
- More complex annotation format

---

### LVIS (Large Vocabulary Instance Segmentation)

**Website:** https://www.lvisdataset.org/  
**License:** Creative Commons Attribution 4.0

**Dataset Details:**
| Property | Value |
|----------|-------|
| Images | 164K |
| Categories | 1200+ |
| Annotations | 2M+ |

**Use Case:** Fine-grained object detection with many categories.

**Advantages:**
- Largest vocabulary (1200+ categories)
- High-quality annotations
- Long-tail distribution

**Considerations:**
- Primarily instance segmentation
- Smaller than COCO for detection

---

## Dataset Selection

### Recommended: COCO

**Rationale:**
1. **Well-Supported**: YOLOv8 pretrained weights available for COCO
2. **Balanced**: Good coverage of common objects
3. **Proven**: Widely used benchmark
4. **Efficient**: Reasonable dataset size

**Pretrained Weights:**
```bash
# YOLOv8n (nano) - fastest
yolov8n.pt

# YOLOv8s (small) - recommended
yolov8s.pt

# YOLOv8m (medium) - higher accuracy
yolov8m.pt

# YOLOv8l (large) - high accuracy
yolov8l.pt

# YOLOv8x (extra-large) - highest accuracy
yolov8x.pt
```

---

## Dataset Formats

### COCO Format

```json
{
  "images": [
    {
      "id": 1,
      "file_name": "image1.jpg",
      "width": 640,
      "height": 480
    }
  ],
  "annotations": [
    {
      "id": 1,
      "image_id": 1,
      "category_id": 1,
      "bbox": [x, y, width, height],
      "area": 1000,
      "iscrowd": 0
    }
  ],
  "categories": [
    {
      "id": 1,
      "name": "person",
      "supercategory": "person"
    }
  ]
}
```

### YOLO Format

```
# Directory structure
dataset/
├── images/
│   ├── train/
│   └── val/
├── labels/
│   ├── train/
│   └── val/
├── data.yaml
```

```
# data.yaml
nc: 80  # number of classes
names: ['person', 'bicycle', 'car', ...]  # class names

# label format (per image.txt)
# class x_center y_center width height
# values normalized to 0-1
0 0.5 0.5 0.2 0.3
1 0.3 0.7 0.15 0.25
```

---

## Custom Dataset Requirements

### Minimum Requirements

| Requirement | Value |
|-------------|-------|
| Training images | 100+ per class |
| Validation images | 20+ per class |
| Image format | JPEG, PNG |
| Annotation format | COCO or YOLO |

### Quality Guidelines

1. **Diversity**: Include varied lighting, angles, backgrounds
2. **Occlusion**: Include partially occluded objects
3. **Scale**: Include objects at various scales
4. **Annotation**: Accurate bounding boxes, no missing objects

---

## Dataset Storage

### Local Storage

```bash
# Recommended directory structure
librarian/
├── models/
│   ├── yolov8s.pt
│   └── yolov8m.pt
├── data/
│   └── object_detection/
│       ├── train/
│       ├── val/
│       └── data.yaml
```

### Cloud Storage (Future)

Consider cloud storage for:
- Large custom datasets
- Pre-trained model weights
- Annotated images

---

## Pre-trained Models

### From Ultralytics

```python
from ultralytics import YOLO

# Load pretrained model
model = YOLO('yolov8s.pt')

# Fine-tune on custom data
model.train(data='custom_data.yaml', epochs=100)
```

### Model Zoo

| Model | Size | COCO mAP | Inference Speed |
|-------|------|----------|-----------------|
| YOLOv8n | 6MB | 37.3% | 128 img/s |
| YOLOv8s | 22MB | 44.9% | 68 img/s |
| YOLOv8m | 52MB | 50.2% | 36 img/s |
| YOLOv8l | 87MB | 52.9% | 20 img/s |
| YOLOv8x | 136MB | 54.3% | 12 img/s |

---

## Data Augmentation

### Standard Augmentations

```python
# YOLOv8 augmentation settings
augmentation:
  hsv_h: 0.015  # Hue augmentation
  hsv_s: 0.7    # Saturation augmentation
  hsv_v: 0.4    # Value augmentation
  degrees: 0.0  # Rotation
  translate: 0.1 # Translation
  scale: 0.5    # Scaling
  shear: 0.0    # Shearing
  perspective: 0.0  # Perspective
  flipud: 0.0   # Vertical flip
  fliplr: 0.5   # Horizontal flip
  mosaic: 1.0   # Mosaic augmentation
  mixup: 0.0    # Mixup augmentation
```

### Custom Augmentations

For specialized use cases:
- Solar panels: Night/thermal imagery
- Drones: Various altitudes
- Safety equipment: Industrial settings

---

## Related Documentation

- [Object Detection Architecture](./architecture.md)
- [Object Detection Capabilities](./capabilities.md)
- [YOLOv8 Documentation](https://docs.ultralytics.com/)