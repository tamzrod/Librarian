# Plugin Palette Manager Roadmap

**Version**: 1.0  
**Last Updated**: 2026-07-05

---

## Vision

Librarian is evolving toward a generalized evidence processing platform with a Node-RED-like plugin palette system. Users will be able to:

1. Discover available plugins
2. Enable/disable capabilities
3. Install new plugins from a marketplace
4. Design custom processing pipelines
5. Create conditional workflows

## Inspiration

| Platform | Key Feature | Librarian Analogy |
|----------|-------------|-------------------|
| Node-RED | Visual flow editor | Pipeline designer |
| Home Assistant | One-click integrations | Plugin installer |
| TrueNAS | App catalog | Plugin marketplace |
| Portainer | Container management | Runtime controls |
| Apache NiFi | Data flow programming | Processing pipelines |
| KNIME | Visual analytics | Evidence workflows |

---

## Phase Roadmap

```
┌─────────────────────────────────────────────────────────────────┐
│                    Librarian Plugin Evolution                      │
└─────────────────────────────────────────────────────────────────┘

Phase 1: Toggle        Phase 2: Discovery    Phase 3: Installer    Phase 4: Pipeline
┌─────────────┐      ┌─────────────┐       ┌─────────────┐      ┌─────────────┐
│ Enable/     │ ───► │ Visible     │ ────► │ Installable  │ ───► │ Pipeline    │
│ Disable     │      │ All States  │       │ Marketplace  │      │ Designer    │
└─────────────┘      └─────────────┘       └─────────────┘      └─────────────┘
       │                   │                      │                     │
       ▼                   ▼                      ▼                     ▼
   Current ✅           Current ✅            Future 📋             Future 🎨
```

---

## Phase 1: Plugin Toggles in Settings

**Status**: ✅ Implemented

Simple enable/disable toggles for configured plugins.

### Features

- Toggle switches for each plugin
- Immediate effect on job scheduling
- Configuration persisted to `config/plugins.yaml`

### UI Mockup

```
┌─────────────────────────────────────────────┐
│ Settings > Plugins                          │
├─────────────────────────────────────────────┤
│ Photo Metadata     [✓]  Enabled            │
│ Thumbnail          [ ]  Disabled           │
│ Object Detection   [ ]  Disabled           │
└─────────────────────────────────────────────┘
```

### Technical Implementation

- `registry/plugin_registry.py` - PluginRegistry class
- `api/routes/settings.py` - Toggle API endpoints
- `config/plugins.yaml` - Configuration storage

---

## Phase 2: Visibility of All Plugins

**Status**: ✅ Implemented

Show all plugins regardless of dependency state.

### Features

- All defined plugins visible in Settings
- Status badges indicate state
- Missing dependencies shown
- Error messages displayed
- Disabled toggles for non-togglable states

### UI Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│ Settings > Plugins                                              │
├─────────────────────────────────────────────────────────────────┤
│ Metadata                                                       │
│   Photo Metadata        [✓]  ✅ Enabled                        │
│   Document Metadata     [ ]  ❌ Not Implemented                 │
├─────────────────────────────────────────────────────────────────┤
│ Vision                                                         │
│   Thumbnail            [✓]  ✅ Enabled                        │
│   Object Detection     [ ]  ⚠️ Missing Dependencies           │
│                       Requires: [ultralytics]                   │
│   OCR                  [ ]  ❌ Not Implemented                 │
│   Face Recognition     [ ]  ❌ Not Implemented                 │
├─────────────────────────────────────────────────────────────────┤
│ Audio                                                          │
│   Transcription        [ ]  ❌ Not Implemented                 │
├─────────────────────────────────────────────────────────────────┤
│ AI                                                             │
│   Embeddings           [ ]  ⚠️ Missing Dependencies           │
│                       Requires: [sentence-transformers, openai] │
└─────────────────────────────────────────────────────────────────┘
```

### Technical Implementation

- `PluginStatus` enum with all states
- `_discover_all_plugins()` for dependency checking
- `_check_missing_packages()` for import detection
- Updated API response with `status`, `missing_dependencies`, `error_message`

---

## Phase 3: Installable Plugin Palette

**Status**: 📋 Planned

Plugin marketplace with one-click installation.

### Features

- Browse available plugins
- View plugin details (description, dependencies, reviews)
- One-click installation
- Automatic dependency resolution
- Update management

### UI Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│ Plugin Palette Manager                                          │
├─────────────────────────────────────────────────────────────────┤
│ [All] [Metadata] [Vision] [Audio] [AI]        [🔍 Search]     │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Object Detection                              [📥 Install]  │ │
│ │ Vision • by Librarian Team • v1.0.0                        │ │
│ │ Detect objects in images using YOLOv8                      │ │
│ │                                                             │ │
│ │ Dependencies:                                               │ │
│ │   [ultralytics] (will be installed)                        │ │
│ │   [torch] (optional, for GPU acceleration)                  │ │
│ │                                                             │ │
│ │ Stats: 12.5k installs • ★★★★☆ (47 reviews)               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ OCR (Tesseract)                            [📥 Install]    │ │
│ │ Vision • by Librarian Team • v1.0.0                        │ │
│ │ Extract text from images and documents                      │ │
│ │                                                             │ │
│ │ Dependencies:                                               │ │
│ │   [pytesseract] (will be installed)                       │ │
│ │   [tesseract] (system package)                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Technical Requirements

#### Plugin Manifest

```python
# plugin_manifest.json
{
    "name": "object_detection",
    "version": "1.0.0",
    "display_name": "Object Detection",
    "description": "Detect objects in images using YOLOv8",
    "author": "Librarian Team",
    "category": "vision",
    
    "package": {
        "name": "librarian-plugin-object-detection",
        "registry": "pypi",  // or "github", "custom"
    },
    
    "dependencies": {
        "required": ["ultralytics>=8.0.0"],
        "optional": ["torch>=2.0.0"],
        "system": ["tesseract"],  // if applicable
    },
    
    "models": [
        {
            "name": "yolov8n",
            "url": "...",
            "size_mb": 6
        }
    ],
    
    "permissions": ["filesystem:read"],
    
    "settings": {
        "confidence_threshold": 0.5,
        "max_detections": 100
    }
}
```

#### Installation Flow

```
User clicks "Install"
        │
        ▼
┌───────────────────────┐
│ Check permissions    │
└───────────┬───────────┘
            │ OK
            ▼
┌───────────────────────┐
│ Download package      │
│ (pip install)         │
└───────────┬───────────┘
            │ Success
            ▼
┌───────────────────────┐
│ Download models       │
└───────────┬───────────┘
            │ Complete
            ▼
┌───────────────────────┐
│ Register plugin       │
│ - Create worker       │
│ - Run migrations      │
└───────────┬───────────┘
            │ Done
            ▼
┌───────────────────────┐
│ Show in Settings      │
│ (enabled by default) │
└───────────────────────┘
```

### Plugin Registry

```
┌──────────────────────────────────────────┐
│           Plugin Registry                 │
├──────────────────────────────────────────┤
│  Local Registry (built-in)                │
│    - photo_metadata                       │
│    - thumbnail                           │
│    - object_detection                     │
│                                          │
│  Installed (user-installed)               │
│    - face_recognition                    │
│    - ocr                                  │
│                                          │
│  Available (marketplace)                  │
│    - license_plate                       │
│    - audio_transcription                  │
└──────────────────────────────────────────┘
```

---

## Phase 4: Processing Pipeline Designer

**Status**: 🎨 Future Vision

Visual pipeline builder for complex workflows.

### Features

- Drag-and-drop plugin arrangement
- Connect plugins in sequence
- Preview data flow
- Test pipelines with sample data
- Save/load pipeline configurations

### UI Mockup

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Pipeline Designer                                    [Save] [Run] [Test] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│   │ Discover │───►│ Thumbnail│───►│Metadata  │───►│Objects   │         │
│   │ Files    │    │          │    │ EXIF     │    │ Detect   │         │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘         │
│                                                │                        │
│                                                ▼                        │
│                                           ┌──────────┐                  │
│                                           │ OCR      │                  │
│                                           │          │                  │
│                                           └──────────┘                  │
│                                                │                        │
│                                                ▼                        │
│                                           ┌──────────┐                  │
│                                           │Embeddings│                  │
│                                           │          │                  │
│                                           └──────────┘                  │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ Node Palette                    │ Pipeline Settings                     │
│ ┌─────────────────────────┐    │ ┌─────────────────────────────────┐  │
│ │ 📷 Metadata              │    │ │ Trigger:                        │  │
│ │   • Photo Metadata        │    │ │ [On file discovery    ▼]       │  │
│ │   • Document Metadata     │    │ │                                 │  │
│ │ 👁️ Vision                 │    │ │ Conditions:                    │  │
│ │   • Object Detection      │    │ │ [✓] Images only               │  │
│ │   • OCR                   │    │ │ [✓] Files > 1KB               │  │
│ │   • Face Recognition      │    │ │                                 │  │
│ │ 🎧 Audio                  │    │ │ Concurrency:                   │  │
│ │   • Transcription         │    │ │ [10 parallel    ▼]             │  │
│ │ 🔢 AI                     │    │ │                                 │  │
│ │   • Embeddings            │    │ └─────────────────────────────────┘  │
│ └─────────────────────────┘    │                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Pipeline Definition Schema

```yaml
# pipeline.yaml
name: "Evidence Extraction Pipeline"
description: "Full processing for image evidence"
trigger:
  type: "on_discovery"
  conditions:
    - type: "file_type"
      in: ["jpg", "jpeg", "png", "heic"]
    - type: "file_size"
      min: 1024  # 1KB minimum

stages:
  - name: "thumbnail"
    plugin: "thumbnail"
    config:
      size: [300, 300]
      
  - name: "metadata"
    plugin: "photo_metadata"
    config:
      extract_gps: true
      extract_camera: true
      
  - name: "objects"
    plugin: "object_detection"
    config:
      confidence_threshold: 0.5
    conditions:
      - type: "file_type"
        in: ["jpg", "jpeg", "png"]
        
  - name: "ocr"
    plugin: "ocr"
    conditions:
      - type: "file_type"
        in: ["jpg", "jpeg", "png", "pdf"]
        
  - name: "embeddings"
    plugin: "embeddings"
    config:
      model: "all-MiniLM-L6-v2"

concurrency:
  max_parallel: 10
  queue_strategy: "priority"  # or "fifo", "size_based"
```

---

## Phase 5: Conditional Workflows

**Status**: 🎨 Future Vision

IF-THEN-ELSE logic for plugins.

### Features

- Conditional plugin execution
- Branching paths based on content
- Loop detection and handling
- Error recovery paths
- Workflow templates

### UI Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│ Conditional Workflow Designer                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐                                               │
│   │  Discover   │                                               │
│   └──────┬──────┘                                               │
│          │                                                      │
│          ▼                                                      │
│   ┌─────────────┐                                               │
│   │ Thumbnail   │                                               │
│   └──────┬──────┘                                               │
│          │                                                      │
│          ▼                                                      │
│   ┌─────────────────────────────────────┐                       │
│   │ IF file_type IN [jpg, png, heic]    │                       │
│   ├─────────────────────────────────────┤                       │
│   │ THEN                                 │                       │
│   │   ├─► Object Detection               │                       │
│   │   └─► OCR                            │                       │
│   │ ELSE                                 │                       │
│   │   └─► Document Parser                │                       │
│   └─────────────────────────────────────┘                       │
│          │                                                      │
│          ▼                                                      │
│   ┌─────────────┐                                               │
│   │ Embeddings  │                                               │
│   └─────────────┘                                               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ Condition Builder                                               │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ [+ Add Condition]                                          │   │
│ │                                                            │   │
│ │ ┌──────────────────────────────────────────────────────┐   │   │
│ │ │ File Type        ▼   IN   [jpg, jpeg, png, heic]     │   │   │
│ │ │                               [x] Remove            │   │   │
│ │ └──────────────────────────────────────────────────────┘   │   │
│ │                                                            │   │
│ │ ┌──────────────────────────────────────────────────────┐   │   │
│ │ │ GPS Present     ▼   =    true                        │   │   │
│ │ │                               [x] Remove            │   │   │
│ │ └──────────────────────────────────────────────────────┘   │   │
│ │                                                            │   │
│ │ [+ Add Group]  AND ▼                                       │   │
│ └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Condition Types

| Condition | Description | Example |
|-----------|-------------|---------|
| `file_type` | Match by extension | `file_type IN [jpg, png]` |
| `file_size` | Size constraints | `file_size > 1024 AND < 10485760` |
| `has_gps` | GPS metadata present | `has_gps = true` |
| `has_text` | Text content detected | `has_text > 50` |
| `duration` | Video/audio length | `duration > 300` |
| `mime_type` | MIME type match | `mime_type STARTS_WITH 'image/'` |
| `filename` | Pattern matching | `filename MATCHES 'IMG_\d{4}'` |
| `contains` | Content inspection | `contains 'receipt'` |

### Example Workflows

#### Image Evidence Workflow

```yaml
workflow: "Image Evidence Processing"
trigger:
  type: "on_discovery"
  conditions:
    - type: "file_type"
      in: ["jpg", "jpeg", "png", "heic", "webp", "tiff"]

stages:
  # Always run
  - name: "thumbnail"
    plugin: "thumbnail"
    
  - name: "metadata"
    plugin: "photo_metadata"
    
  # Conditional branches
  - name: "detection_branch"
    type: "conditional"
    condition:
      type: "file_type"
      in: ["jpg", "jpeg", "png", "heic"]
    then:
      - name: "object_detection"
        plugin: "object_detection"
        
  # OCR for images with potential text
  - name: "ocr_branch"
    type: "conditional"
    condition:
      type: "file_size"
      min: 1024  # Skip tiny thumbnails
    then:
      - name: "ocr"
        plugin: "ocr"
        
  # Always embed
  - name: "embeddings"
    plugin: "embeddings"
```

#### Video Evidence Workflow

```yaml
workflow: "Video Evidence Processing"
trigger:
  type: "on_discovery"
  conditions:
    - type: "file_type"
      in: ["mp4", "mov", "avi", "mkv"]

stages:
  - name: "video_metadata"
    plugin: "video_metadata"
    
  - name: "transcription_branch"
    type: "conditional"
    condition:
      type: "duration"
      min: 60  # Only transcribe videos > 1 minute
      max: 3600  # Skip very long videos
    then:
      - name: "transcription"
        plugin: "transcription"
        
  - name: "frame_extraction"
    plugin: "frame_extractor"
    config:
      interval_seconds: 30  # Extract frame every 30 seconds
```

---

## Comparison with Inspiration Platforms

### Node-RED Comparison

| Feature | Node-RED | Librarian Pipeline |
|---------|----------|-------------------|
| Visual editor | ✅ Canvas | 🔄 Future |
| Nodes | 3,500+ | Built-in only |
| Wiring | JSONata | YAML |
| Deployment | Dashboard | API |
| Testing | Inject/Debug | Test data |

### Home Assistant Comparison

| Feature | Home Assistant | Librarian Palette |
|---------|----------------|-------------------|
| Discovery | Auto-discovery | Manual config |
| Install | One-click | Future one-click |
| Config | YAML/GUI | YAML/UI |
| Updates | Auto | Manual |
| Community | Huge | Growing |

### Apache NiFi Comparison

| Feature | NiFi | Librarian Pipeline |
|---------|------|-------------------|
| Scale | Enterprise | Personal/SMB |
| UI | Web-based | Web-based |
| Data flow | Real-time | Batch/event |
| Backpressure | Built-in | Future |
| Clustering | Yes | Future |

---

## Implementation Priority

| Phase | Priority | Effort | Value | Status |
|-------|----------|--------|-------|--------|
| 1. Toggles | P0 | Low | Medium | ✅ Done |
| 2. Visibility | P0 | Low | High | ✅ Done |
| 3. Installer | P1 | High | High | 📋 Planned |
| 4. Pipeline | P2 | Very High | Very High | 🎨 Vision |
| 5. Conditional | P2 | Very High | Very High | 🎨 Vision |

---

## Future Considerations

### Marketplace

- Hosted plugin registry
- Version management
- Dependency resolution
- Security scanning
- User reviews/ratings

### Enterprise Features

- Plugin signing
- Air-gapped installation
- Custom plugin approval
- Audit logging
- Role-based access

### Developer Tools

- Plugin scaffolding
- Local registry
- CI/CD templates
- Documentation generator
- Testing framework

---

## Summary

Librarian is building toward a comprehensive evidence processing platform where:

1. **Phase 1-2**: Visibility and control (current)
2. **Phase 3**: Extensibility via marketplace
3. **Phase 4**: Visual pipeline building
4. **Phase 5**: Intelligent automation

The roadmap prioritizes user value while maintaining system simplicity.

---

*This document outlines the long-term vision for Librarian's plugin palette system.*
