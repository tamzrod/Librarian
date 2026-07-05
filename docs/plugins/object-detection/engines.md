# Object Detection Engines

**Plugin:** Object Detection  
**Status:** 📋 Architecture Planning  
**Purpose:** Document supported engines and their characteristics

---

## Overview

The Object Detection plugin architecture supports multiple detection engines. This document describes candidate engines, their strengths and weaknesses, and the abstraction that allows any engine to be used.

**Philosophy:** Librarian does not recommend an implementation. The architecture must support all engines. Consumers decide which engine to use based on their requirements.

---

## Engine Abstraction

```
┌─────────────────────────────────────────────────────────────┐
│                 Object Detection Plugin                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Plugin Interface                      │   │
│  │  - Input: Image file                                   │   │
│  │  - Output: Detection metadata (label, confidence, bbox)│   │
│  └──────────────────────────────────────────────────────┘   │
│                              │                               │
│              ┌───────────────┼───────────────┐               │
│              │               │               │               │
│              ▼               ▼               ▼               │
│        ┌─────────┐    ┌──────────┐    ┌─────────┐           │
│        │  YOLO   │    │Grounding │    │  OWL-   │           │
│        │  v8     │    │  DINO    │    │   ViT   │           │
│        └─────────┘    └──────────┘    └─────────┘           │
│              │               │               │               │
│              │               │               │               │
│              └───────────────┴───────────────┘               │
│                              │                               │
│                              ▼                               │
│        ┌─────────────────────────────────────────────┐       │
│        │          Common Output Schema                │       │
│        │  { plugin, engine, objects[], ... }         │       │
│        └─────────────────────────────────────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Interface Contract

All engines must produce output conforming to the standard metadata schema:

```json
{
  "plugin": "object-detection",
  "engine": "<engine-name>",
  "objects": [
    {
      "label": "string",
      "confidence": 0.0-1.0,
      "bbox": [x, y, width, height]
    }
  ]
}
```

---

## Candidate Engines

### 1. YOLOv8 (Ultralytics)

**Repository:** https://github.com/ultralytics/ultralytics  
**License:** AGPL-3.0

**Characteristics:**

| Aspect | Details |
|--------|---------|
| Architecture | One-stage detector, anchor-based |
| Model Variants | n, s, m, l, x (increasing size/accuracy) |
| Pretrained Classes | 80 COCO classes |
| Speed | Very fast (especially smaller models) |
| Accuracy | Good (especially larger models) |
| Model Size | 6MB (nano) to 136MB (x-large) |

**Strengths:**
- Excellent inference speed, especially on CPU
- Mature, well-tested implementation
- Large pretrained model zoo
- Easy to fine-tune on custom data
- Good community support and documentation

**Weaknesses:**
- Fixed class set (cannot detect arbitrary objects)
- Anchor-based design may miss unusual aspect ratios
- Fine-tuning requires labeled bounding box data

**Use Cases:**
- Real-time processing requirements
- General-purpose object detection
- When pretrained weights are sufficient
- CPU-only deployment

---

### 2. Grounding DINO (IDEA-Research)

**Repository:** https://github.com/IDEA-Research/Grounding-DINO  
**License:** Apache-2.0

**Characteristics:**

| Aspect | Details |
|--------|---------|
| Architecture | Two-stage detector, transformer-based |
| Input | Text prompts + images |
| Pretrained Classes | Open-vocabulary (any text-described class) |
| Speed | Moderate (transformer overhead) |
| Accuracy | High on novel classes |
| Model Size | ~1.3GB (large model) |

**Strengths:**
- Open-vocabulary detection (detect anything you can text-prompt)
- Zero-shot capability on novel classes
- Strong performance on rare/specialized objects
- Combines language understanding with detection

**Weaknesses:**
- Slower inference than one-stage detectors
- Requires text prompts (adds configuration complexity)
- Higher memory usage
- More complex to deploy

**Use Cases:**
- Detecting specialized or rare objects
- When class set is not fixed
- Zero-shot detection scenarios
- Research applications

---

### 3. OWL-ViT (Google)

**Repository:** https://github.com/huggingface/transformers  
**Paper:** https://arxiv.org/abs/2205.06230  
**License:** Apache-2.0

**Characteristics:**

| Aspect | Details |
|--------|---------|
| Architecture | Vision Transformer (ViT) |
| Input | Text queries + images |
| Pretrained Classes | Open-vocabulary |
| Speed | Moderate (ViT inference) |
| Accuracy | Good on natural images |
| Model Size | ~1GB |

**Strengths:**
- Hugging Face integration (easy deployment)
- Open-vocabulary detection
- Simple text-prompt interface
- Good for zero-shot detection

**Weaknesses:**
- Slower than YOLO on standard classes
- May require prompt engineering for best results
- Transformer inference is memory-intensive

**Use Cases:**
- Hugging Face ecosystem integration
- Open-vocabulary detection needs
- When ease of deployment is prioritized

---

### 4. RT-DETR (Baidu)

**Repository:** https://github.com/lyuwenyu/RT-DETR  
**Paper:** https://arxiv.org/abs/2304.08069  
**License:** Apache-2.0

**Characteristics:**

| Aspect | Details |
|--------|---------|
| Architecture | Real-Time DETR (transformer) |
| Model Variants | Small, Medium, Large |
| Pretrained Classes | COCO classes |
| Speed | Fast for transformer-based |
| Accuracy | High (transformer attention) |
| Model Size | ~115MB (large) |

**Strengths:**
- Real-time performance with transformer accuracy
- No NMS required (attention-based deduplication)
- Good balance of speed and accuracy
- Stable training (no anchor matching issues)

**Weaknesses:**
- Newer, less community support
- Fewer pretrained weights than YOLO
- Higher memory usage than YOLO
- Less mature ecosystem

**Use Cases:**
- When transformer accuracy is needed with real-time speed
- Applications requiring attention visualization
- Modern deployment seeking best speed/accuracy trade-off

---

## Engine Comparison

### Performance Characteristics

| Engine | Speed | Accuracy | Memory | Flexibility |
|--------|-------|----------|--------|-------------|
| YOLOv8n | Fastest | Lower | Lowest | Fixed classes |
| YOLOv8s | Fast | Medium | Low | Fixed classes |
| YOLOv8m | Medium | Higher | Medium | Fixed classes |
| Grounding DINO | Slow | High | High | Open-vocabulary |
| OWL-ViT | Moderate | Good | High | Open-vocabulary |
| RT-DETR | Fast | High | Medium | Fixed classes |

### Class Flexibility

| Engine | Fixed Classes | Open-Vocabulary | Custom Training |
|--------|---------------|-----------------|-----------------|
| YOLOv8 | 80 COCO | ❌ | ✅ Fine-tune |
| Grounding DINO | ✅ Any | ✅ Text prompts | ✅ Fine-tune |
| OWL-ViT | ✅ Any | ✅ Text prompts | ✅ Fine-tune |
| RT-DETR | 80 COCO | ❌ | ✅ Fine-tune |

---

## Engine Selection Considerations

The choice of engine depends on the specific use case. Consider these factors:

### Choose YOLOv8 when:
- Speed is critical (real-time, high-volume processing)
- Detecting standard COCO classes is sufficient
- CPU-only deployment is required
- Well-understood, stable deployment is needed

### Choose Grounding DINO when:
- Detecting arbitrary/custom classes is required
- Zero-shot detection on novel objects is needed
- Class set is not known at training time
- Research on open-vocabulary detection

### Choose OWL-ViT when:
- Hugging Face ecosystem is preferred
- Open-vocabulary detection with simple interface
- Zero-shot detection on custom classes

### Choose RT-DETR when:
- Transformer accuracy with real-time speed
- Attention mechanisms for interpretability needed
- Modern architecture is preferred over CNN

---

## Future Engines

The plugin architecture must support future engines. New engines should:

1. **Implement the standard interface**: Accept image input, produce standardized output
2. **Conform to metadata schema**: Output labels, confidence scores, bounding boxes
3. **Register in plugin configuration**: Add to `config/plugins.yaml`
4. **Document capabilities**: Add to this file with strengths/weaknesses

### Adding a New Engine

```yaml
# config/plugins.yaml
plugins:
  object_detection:
    enabled: true
    engine: <engine-name>
    # Engine-specific configuration
```

### Engine Registration

Each engine should register with metadata:

```python
class ObjectDetectionEngine(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Engine identifier (e.g., 'yolo-v8n', 'grounding-dino-s')"""
        
    @property
    @abstractmethod
    def supported_classes(self) -> List[str]:
        """List of classes this engine can detect"""
        
    @abstractmethod
    def detect(self, image_path: str) -> DetectionResult:
        """Run detection on image"""
```

---

## No Winner Selection

**Librarian's position:** No engine is universally superior.

Different engines serve different needs:

| Requirement | Recommended Engines |
|-------------|---------------------|
| Speed priority | YOLOv8n, YOLOv8s |
| Accuracy priority | Grounding DINO, RT-DETR |
| Flexibility priority | Grounding DINO, OWL-ViT |
| Memory priority | YOLOv8n, YOLOv8s |
| Production stability | YOLOv8 |

The architecture supports all of these. Implementors choose based on their requirements.

---

## Related Documentation

- [Object Detection README](./README.md)
- [Object Detection Architecture](./architecture.md)
- [Object Detection Metadata Schema](./metadata-schema.md)
- [Plugin Contract](./plugin-contract.md)
