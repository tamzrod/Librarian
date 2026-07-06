# Plugin Dependency Management

**Version**: 1.0  
**Last Updated**: 2026-07-05

---

## Overview

Librarian plugins may require various types of dependencies:

- Python packages (PyPI)
- Machine learning models
- GPU drivers and CUDA
- System libraries
- Docker containers

This document outlines the philosophy, detection mechanisms, and management strategies for these dependencies.

## Dependency Philosophy

### Core Principles

1. **Visibility Over Concealment**
   - Plugins should be visible regardless of dependency state
   - Missing dependencies should guide users toward resolution
   - No silent failures or hidden limitations

2. **Progressive Enhancement**
   - Core functionality works without optional dependencies
   - Advanced features unlock with additional packages
   - Graceful degradation when dependencies unavailable

3. **Explicit Over Implicit**
   - Dependencies declared in plugin manifest
   - Installation requirements clearly documented
   - Version constraints specified

4. **Container-Aware Design**
   - Dependencies may require image rebuild
   - Some packages need GPU runtime
   - Consider CI/CD pipeline implications

## Dependency Categories

### 1. Python Packages

Standard Python dependencies from PyPI.

**Examples**:
| Plugin | Package | Purpose |
|--------|---------|---------|
| Object Detection | `ultralytics` | YOLOv8 model |
| OCR | `pytesseract` | Tesseract bindings |
| Transcription | `openai-whisper` | Whisper model |
| Embeddings | `sentence-transformers` | Vector embeddings |

**Detection**:
```python
def _check_missing_packages(packages: list) -> list:
    import importlib
    missing = []
    for package in packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing.append(package)
    return missing
```

**Installation**:
```bash
pip install ultralytics
```

---

### 2. Model Dependencies

Machine learning models required for inference.

**Examples**:
| Plugin | Model | Size | Notes |
|--------|-------|------|-------|
| Object Detection | `yolov8n.pt` | ~6MB | Downloaded on first use |
| Face Recognition | `dlib_face_model` | ~100MB | Pre-trained weights |
| Transcription | `whisper-base` | ~300MB | Model downloaded |

**Detection**: Check if model files exist or can be downloaded.

**Installation**:
- Models often auto-download on first run
- May need explicit download step
- Consider offline/firewalled environments

**Caching**:
```
~/.cache/
├── ultralytics/
│   └── yolov8n.pt
├── whisper/
│   └── base.pt
└── sentence-transformers/
    └── all-MiniLM-L6-v2/
```

---

### 3. GPU Dependencies

Graphics processing unit requirements for accelerated inference.

**Requirements**:
| Package | Minimum | Recommended |
|---------|---------|-------------|
| CUDA | 11.8 | 12.x |
| cuDNN | 8.x | 8.9+ |
| NVIDIA Driver | 525.x | 535.x |

**Detection**:
```python
def check_gpu_available() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False
```

**Behavior**:
- CPU fallback when GPU unavailable
- Warning logs for GPU-related issues
- Performance degradation documentation

---

### 4. System Dependencies

OS-level packages and libraries.

**Examples**:
| Package | Purpose | OS |
|---------|---------|-----|
| `tesseract` | OCR engine | Linux/macOS |
| `libgl1` | OpenCV display | Linux |
| `ffmpeg` | Video processing | All |
| `imagemagick` | Image conversion | All |

**Detection**:
```bash
# Check for tesseract
which tesseract && tesseract --version

# Check for ffmpeg
which ffmpeg && ffmpeg -version
```

**Installation**:
```bash
# Ubuntu/Debian
apt-get install tesseract-ocr ffmpeg

# macOS
brew install tesseract ffmpeg

# Alpine
apk add tesseract fesseract ffmpeg
```

---

### 5. Docker Dependencies

Containerized services that plugins may depend on.

**Examples**:
| Service | Purpose | Port |
|---------|---------|------|
| `postgres` | Database | 5432 |
| `redis` | Job queue | 6379 |
| `milvus` | Vector store | 19530 |
| `minio` | Object storage | 9000 |

**Detection**:
```bash
docker ps | grep <service_name>
```

**Installation**:
```bash
docker run -d --name <service> <image>
```

---

## Required vs Optional Dependencies

### Required Dependencies

Dependencies that must be present for the plugin to function.

**Characteristics**:
- No fallback behavior
- Plugin shows `missing_dependencies` status
- Cannot be enabled without installation

**Example**:
```python
PLUGIN_DEFINITIONS = {
    'object_detection': {
        'required_packages': ['ultralytics'],  # Required
        'optional_packages': ['torch'],  # Optional
    }
}
```

---

### Optional Dependencies

Dependencies that enhance functionality but aren't strictly required.

**Characteristics**:
- Plugin works in degraded mode without them
- May show informational message
- User can install to unlock features

**Example**:
```python
PLUGIN_DEFINITIONS = {
    'embeddings': {
        'required_packages': [],
        'optional_packages': [
            'openai',      # For OpenAI embeddings
            'sentence-transformers',  # For local embeddings
        ],
    }
}
```

---

## Dependency Declaration

### Plugin Manifest Schema

```python
{
    'name': 'object_detection',
    'required_packages': ['ultralytics'],
    'optional_packages': ['torch', 'gpu_util'],
    'system_dependencies': [],  # Future
    'models': [
        {
            'name': 'yolov8n',
            'url': 'https://ultralytics.com/models/yolov8n.pt',
            'size_mb': 6,
            'hash': 'sha256:abc123...',
        }
    ],
    'gpu_required': False,
    'gpu_optional': True,
}
```

---

## Container Rebuild Considerations

Some dependencies require rebuilding the Docker image.

### When Rebuild Required

| Dependency Type | Rebuild Required | Reason |
|----------------|-----------------|--------|
| Python packages | No | Can pip install |
| System packages | Yes | Need apt-get |
| GPU drivers | Yes | Kernel level |
| CUDA libraries | Yes | Version specific |
| Models | No | Auto-download |

### Recommended Approach

1. **Base Image Selection**
   - Choose image with CUDA pre-installed for GPU plugins
   - Use Alpine for minimal footprint where GPU not needed

2. **Multi-Stage Build**
   ```dockerfile
   FROM python:3.11-slim AS base
   
   # Install system deps
   RUN apt-get update && apt-get install -y \
       tesseract-ocr \
       ffmpeg \
       libgl1-mesa-glx
   
   # Install Python deps
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   # Download models (optional)
   RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
   ```

3. **Runtime Installation**
   ```dockerfile
   # For optional packages that don't need rebuild
   RUN pip install --no-cache-dir ultralytics
   ```

---

## Visibility Principles

### Why Show Plugins Without Dependencies?

1. **Discoverability**
   - Users can see what capabilities exist
   - Future planning includes these plugins
   - Marketing visibility for features

2. **Guidance**
   - Clear path to enable functionality
   - No guesswork about why plugin is hidden
   - Links to installation instructions

3. **Transparency**
   - No hidden limitations
   - Expectations set clearly
   - Trust in the platform

### Example User Experience

**Before (Hidden)**:
```
Settings > Plugins
┌─────────────────────┐
│ Photo Metadata  [✓] │
│ Thumbnail      [ ]  │
└─────────────────────┘
User: "Where's object detection?"
```

**After (Visible)**:
```
Settings > Plugins
┌─────────────────────────────────────┐
│ Photo Metadata           [✓]        │
│ Thumbnail              [ ]          │
├─────────────────────────────────────┤
│ Vision                                 │
│   Object Detection          [ ]       │
│   Status: Missing Dependencies         │
│   Requires: [ultralytics]             │
└─────────────────────────────────────┘
User: "I see there's object detection!
       I need to install ultralytics."
```

---

## Detection Implementation

### At Startup

```python
def _discover_all_plugins() -> dict:
    for plugin_name, defn in PLUGIN_DEFINITIONS.items():
        status_info = {
            'status': PluginStatus.ENABLED,
            'missing_dependencies': [],
            'error_message': None,
        }
        
        # Check required packages
        required = defn.get('required_packages', [])
        missing = _check_missing_packages(required)
        if missing:
            status_info['status'] = PluginStatus.MISSING_DEPENDENCIES
            status_info['missing_dependencies'] = missing
            status_info['error_message'] = f"Missing packages: {', '.join(missing)}"
        
        # Check system deps (future)
        system_deps = defn.get('system_dependencies', [])
        for dep in system_deps:
            if not _check_system_dependency(dep):
                # Handle missing system dep
                pass
        
        # Check models (future)
        models = defn.get('models', [])
        for model in models:
            if not _check_model_available(model):
                # Handle missing model
                pass
        
        yield plugin_name, status_info
```

---

## Future Enhancements

### Planned Features

1. **System Dependency Detection**
   - Detect tesseract, ffmpeg availability
   - Platform-specific warnings

2. **GPU Detection**
   - CUDA version checking
   - GPU memory estimation

3. **Model Download Status**
   - Show download progress
   - Offline mode indicators

4. **Container Health Checks**
   - Verify dependent services
   - Connection status indicators

5. **Dependency Installation UI**
   - One-click install for pip packages
   - Docker compose integration
   - Model download triggers

---

## Summary

| Dependency Type | Detection | Installation | Rebuild Required |
|----------------|-----------|--------------|-----------------|
| Python packages | ✅ Implemented | `pip install` | No |
| ML models | 🔄 Planned | Auto-download | No |
| GPU/CUDA | 🔄 Planned | Image rebuild | Yes |
| System libs | 🔄 Planned | apt-get | Yes |
| Docker services | 🔄 Planned | docker run | N/A |

---

*This document outlines the dependency management philosophy for Librarian plugins.*
