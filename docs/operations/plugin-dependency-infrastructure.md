# Plugin Dependency Infrastructure

This document describes the persistent storage infrastructure for plugin dependencies and caches in Librarian.

## Overview

Librarian is plugin-centric. AI plugins are only one category of plugins. Examples include:

- Thumbnail
- Photo Metadata
- Object Detection
- OCR
- Transcription
- Embeddings
- Geolocation
- Video Processing
- Future plugins

Some plugins require:
- Python packages
- System packages
- Models
- Language packs
- Runtime assets
- External databases
- Cache files

These are collectively referred to as **Plugin Dependencies** and must not be treated as AI-specific infrastructure.

## Volume Layout

```
deploy/docker/linux/volumes/
├── postgres/
├── library/
├── librarian-data/
├── plugin-dependencies/
└── plugin-cache/
```

## Volume Responsibilities

### /library

**Purpose**: User evidence

**Contents**: User's original files
- Photos
- Videos
- Documents
- Any files the user wants to index

**Lifecycle**: Managed by the user. Librarian reads but never modifies this volume.

### /librarian-data

**Purpose**: Librarian-generated artifacts

**Contents**: Derived data created by Librarian
- Thumbnails
- Extracted metadata
- Embeddings
- Indexes
- Catalogs

**Lifecycle**: Regenerated from /library if deleted. Survives container recreation.

### /plugin-dependencies

**Purpose**: Persistent assets required by plugins

**Contents**: Plugin-specific assets that must survive rebuilds
- Models (YOLOv8n.pt, Whisper models, etc.)
- Language data (tessdata for OCR, GeoIP databases)
- External databases
- Configuration files

**Example Structure**:
```
plugin-dependencies/
├── object-detection/
│   └── yolov8n.pt
├── transcription/
│   └── whisper-base.pt
├── ocr/
│   └── tessdata/
├── geolocation/
│   └── GeoLite2-City.mmdb
├── embeddings/
│   └── sentence-transformers/
└── video/
    └── ffmpeg-assets/
```

**Lifecycle**: Persistent across rebuilds, resets, and upgrades. Only deleted on explicit request.

### /plugin-cache

**Purpose**: Reusable runtime caches

**Contents**: Temporary data that can be regenerated
- pip cache
- Python wheel cache
- Hugging Face cache
- PyTorch model cache
- Transformers cache

**Example Structure**:
```
plugin-cache/
├── pip/
├── wheels/
├── huggingface/
├── torch/
└── transformers/
```

**Lifecycle**: Persistent across rebuilds and upgrades. Can be safely cleared if needed.

## Docker Volumes

The following named volumes are defined in docker-compose.yml:

| Volume | Purpose | Survives rebuild.sh | Survives reset.sh |
|--------|---------|---------------------|-------------------|
| `postgres_data` | PostgreSQL database | Yes | No |
| `librarian_data` | Derived artifacts | Yes | Yes |
| `plugin_dependencies` | Plugin assets | Yes | Yes |
| `plugin_cache` | Runtime caches | Yes | Yes |

## Cache Persistence Environment Variables

The following environment variables are configured for cache persistence:

### PyTorch

| Variable | Default Path | Description |
|----------|--------------|-------------|
| `TORCH_HOME` | `/plugin-cache/torch` | PyTorch model cache |

### Hugging Face

| Variable | Default Path | Description |
|----------|--------------|-------------|
| `HF_HOME` | `/plugin-cache/huggingface` | Hugging Face hub cache |
| `TRANSFORMERS_CACHE` | `/plugin-cache/transformers` | Transformers model cache |

### Python

| Variable | Default Path | Description |
|----------|--------------|-------------|
| `PIP_CACHE_DIR` | `/plugin-cache/pip` | pip download cache |

### Additional Common Variables

| Variable | Purpose |
|----------|---------|
| `PLUGIN_DEPENDENCIES_ROOT` | Base path for plugin dependencies (`/plugin-dependencies`) |
| `PLUGIN_CACHE_ROOT` | Base path for plugin caches (`/plugin-cache`) |

## Implementation

### docker-compose.yml

Both the main `deploy/docker-compose.yml` and `deploy/docker/linux/docker-compose.yml` include:

```yaml
services:
  librarian-api:
    environment:
      - PLUGIN_DEPENDENCIES_ROOT=/plugin-dependencies
      - PLUGIN_CACHE_ROOT=/plugin-cache
      - TORCH_HOME=/plugin-cache/torch
      - HF_HOME=/plugin-cache/huggingface
      - TRANSFORMERS_CACHE=/plugin-cache/transformers
      - PIP_CACHE_DIR=/plugin-cache/pip
    volumes:
      - plugin_dependencies:/plugin-dependencies:rw
      - plugin_cache:/plugin-cache:rw

  librarian-worker:
    environment:
      - PLUGIN_DEPENDENCIES_ROOT=/plugin-dependencies
      - PLUGIN_CACHE_ROOT=/plugin-cache
      - TORCH_HOME=/plugin-cache/torch
      - HF_HOME=/plugin-cache/huggingface
      - TRANSFORMERS_CACHE=/plugin-cache/transformers
      - PIP_CACHE_DIR=/plugin-cache/pip
    volumes:
      - plugin_dependencies:/plugin-dependencies:rw
      - plugin_cache:/plugin-cache:rw

volumes:
  plugin_dependencies:
    driver: local
  plugin_cache:
    driver: local
```

## Data Lifecycle

### Evidence Lifecycle

1. User adds files to `/library`
2. Files are scanned and indexed
3. Evidence is stored in PostgreSQL catalog
4. User can delete files from `/library` at any time
5. Librarian catalog remains until explicitly reset

### Generated Artifact Lifecycle

1. Plugins generate derived data (thumbnails, metadata)
2. Artifacts stored in `/librarian-data`
3. Artifacts can be regenerated from `/library`
4. Deleted automatically on `reset.sh`
5. Survives container recreation

### Plugin Dependency Lifecycle

1. Plugin downloads required assets (models, language packs)
2. Assets stored in `/plugin-dependencies`
3. Assets persist across all operations
4. Only deleted on explicit request or volume destruction
5. Survives rebuilds, resets, upgrades, and database recreation

### Cache Lifecycle

1. Runtime creates cache during execution
2. Cache stored in `/plugin-cache`
3. Cache speeds up subsequent operations
4. Can be safely cleared if corrupted
5. Automatically repopulated on next use

## Script Compatibility

### rebuild.sh

- Uses `docker compose down` (preserves volumes)
- Uses `docker compose build --no-cache`
- Uses `docker compose up -d`
- **plugin-dependencies**: Preserved ✓
- **plugin-cache**: Preserved ✓

### reset.sh

- Uses `docker compose down -v` (destroys volumes)
- Uses `docker system prune -f`
- **plugin-dependencies**: Preserved (not named volumes in -v scope)
- **plugin-cache**: Preserved (not named volumes in -v scope)
- Note: The `-v` flag only removes volumes listed in the compose file at the time of down. Since plugin volumes are named volumes, they persist.

### update.sh

- Uses `docker compose down` (preserves volumes)
- Uses `docker compose pull`
- Uses `docker compose up -d --build`
- **plugin-dependencies**: Preserved ✓
- **plugin-cache**: Preserved ✓

## Future Considerations

### Host-Mounted Volumes

For production deployments, consider using host-mounted directories for plugin dependencies and caches:

```yaml
volumes:
  - ${PLUGIN_DEPS_PATH:-./volumes/plugin-dependencies}:/plugin-dependencies:rw
  - ${PLUGIN_CACHE_PATH:-./volumes/plugin-cache}:/plugin-cache:rw
```

This allows:
- Direct access to assets from host
- Backup of models and caches
- Sharing between multiple deployments

### Backup Strategy

Plugin dependencies should be included in backup strategies:
- Models can be large but are stable
- Caches can be regenerated if lost
- Consider backing up plugin-dependencies more frequently

### Multi-Environment Sharing

For development/testing scenarios, plugin caches can be shared:
- Models downloaded once
- Used across multiple test runs
- Speeds up CI/CD pipelines