# ARCHITECTURE.md

## Deployment Model

Librarian is designed for simple, reliable deployment via Docker Compose.

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose                           │
│  ┌─────────────────┐  ┌─────────────────────────────────┐ │
│  │  Librarian API  │  │         PostgreSQL               │ │
│  │    (Port 8001)   │  │                                 │ │
│  └────────┬────────┘  └─────────────────────────────────┘ │
│           │                                                   │
│           │ /library (read-only volume)                      │
│           ↓                                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    Host Filesystem                        ││
│  │              /path/to/documents                          ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Configuration

- Library root: Docker volume mapping (`/path/to/host:/library:ro`)
- Database: Environment variable (`DATABASE_URL`)
- API: Exposed on port 8001

### Single Instance Design

- One library root per deployment
- One PostgreSQL catalog per deployment
- Multiple Librarian instances for multiple libraries

## Single Library Architecture

Librarian operates on a **single library root** at a time.

### Principles

| Principle | Description |
|-----------|-------------|
| **One Root** | Single directory tree per deployment |
| **Recursive Scan** | All subfolders included automatically |
| **Global Configuration** | Exclusion patterns apply to entire library |
| **No Runtime Switching** | Change library via redeployment |

### Directory Structure

```
Library Root (mounted volume)
├── documents/
│   ├── contracts/
│   │   └── abc_contract.pdf
│   └── invoices/
│       └── invoice_001.pdf
├── photos/
│   ├── 2026/
│   │   └── IMG_20260101.jpg
│   └── 2025/
└── notes/
    └── meeting_notes.md
```

### Exclusion Patterns

Configured globally in librarian configuration:
- `.git/` - Version control
- `node_modules/` - Dependencies
- Hidden files (`.` prefix)
- Large binary files (configurable threshold)

## API First Architecture

The REST API is the **public product interface**. All operations are exposed via API.

### API Design Principles

| Principle | Description |
|-----------|-------------|
| **Stable Contract** | API versioning ensures compatibility |
| **Resource Oriented** | Collections, Documents, Entities, Events, Locations, Questions |
| **JSON Responses** | Consistent response format |
| **Cursor Pagination** | Efficient for large datasets |

### API Resources

| Resource | Description |
|----------|-------------|
| `Collections` | Grouping of indexed artifacts |
| `Documents` | Indexed files with metadata |
| `Entities` | Named things (people, organizations, devices) |
| `Events` | Timestamped occurrences |
| `Locations` | Geographic points or named places |
| `Relationships` | Connections between entities |
| `Questions` | Natural language queries |

### Example Deployment

```yaml
services:
  librarian:
    image: librarian/engine:latest
    ports:
      - "8001:8001"
    volumes:
      - /home/user/documents:/library:ro
    environment:
      - DATABASE_URL=postgresql://postgres:secret@db:5432/librarian

  db:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

## Client Architecture

GUI clients communicate exclusively through the REST API. GUI implementations are intentionally **disposable and replaceable**.

### Client Types

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENTS                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   Web    │  │ Desktop  │  │   CLI    │  │   MCP    │  │
│  │   GUI    │  │   GUI    │  │   Tool   │  │  Client  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       └─────────────┴─────────────┴─────────────┘         │
│                           │                                 │
└───────────────────────────┼─────────────────────────────────┘
                            │ REST API (stable contract)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 Librarian Engine                            │
│                    (Core Engine)                             │
└─────────────────────────────────────────────────────────────┘
```

### Client Characteristics

| Client Type | Examples | Purpose |
|-------------|----------|---------|
| Web GUI | React SPA, Vue app | General browsing |
| Desktop GUI | Electron, Tauri | Offline-capable |
| CLI | `librarian` command | Developers, scripts |
| MCP | AI agent integration | Agentic workflows |
| Mobile | React Native, Flutter | On-the-go access |
| Third-party | Custom integrations | Specialized tools |

### Why Disposable GUIs?

1. **GUI paradigms change** - Today's framework is tomorrow's legacy
2. **Specialization** - Different users want different interfaces
3. **Core value** - The evidence engine is the valuable part
4. **Decoupling** - Engine advances independently of UI

## Automatic Ingestion Workflow

Users do not manually trigger ingestion. File changes are automatically detected and processed.

### Artifact Ingestion vs Document Processing

Librarian has evolved from a **Document Processing Platform** to an **Artifact Ingestion Platform**.

| Concept | Document Processing | Artifact Ingestion |
|---------|--------------------|--------------------|
| Focus | Text documents | All file types |
| Ingestion | Parse content | Create artifact record |
| Enrichment | Part of parsing | Independent workers |
| Timeline | Text-based | Artifact-anchored |

### Parser vs Worker Distinction

**Parsers** are responsible for:
- Validating artifact files
- Identifying file types and MIME types
- Extracting inexpensive metadata (dimensions, basic properties)
- Creating the initial document record

**Workers** are responsible for:
- Enriching artifacts with derived information
- Extracting structured data (EXIF, entities, events, locations)
- Generating embeddings
- Processing that may fail independently

Example flow for an image:
```
ImageParser
    ↓
document created (lightweight, fast)

PhotoMetadataWorker (independent)
    ↓
GPS, camera, timestamp extracted

OCRWorker (independent)
    ↓
text extracted from image

ObjectDetectionWorker (independent)
    ↓
objects detected
```

Each worker references the same `document_id`. Workers may fail independently. The artifact remains valid even if one enrichment fails.

### Ingestion Pipeline

```
File Change Detected
        ↓
┌───────────────────┐
│  Filesystem Watcher│
│  (inotify/polling)│
└────────┬──────────┘
         ↓
┌───────────────────┐
│   Parser Router   │
│ (route by type)   │
└────────┬──────────┘
         ↓
┌───────────────────┐
│     Parser        │
│ (artifact record)  │
└────────┬──────────┘
         ↓
┌───────────────────┐
│   PostgreSQL      │
│     Catalog       │
└────────┬──────────┘
         ↓
┌───────────────────┐
│  Workers          │
│ (parallel enrich) │
└───────────────────┘
```

### Watcher Strategy

| Strategy | Description | Fallback |
|----------|-------------|----------|
| Primary | Filesystem watchers (inotify, FSEvents) | Polling |
| Fallback | Polling every 30 seconds | Always available |
| Deduplication | Avoid duplicate processing | Event coalescing |

### Change Types

| Change | Action |
|--------|--------|
| New file | Parse, create artifact, schedule workers |
| Modified file | Re-parse, update catalog |
| Deleted file | Remove from catalog |
| Renamed file | Update path in catalog |

---

## Architectural Layers (Internal)

```
┌─────────────────────────────────────────────────────────────┐
│                        AGENT LAYER                          │
│              (AI Agent Reasoning over Evidence)              │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                    EVIDENCE BUILDER                          │
│         (Assembles evidence packages for queries)            │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                   EXTRACTORS LAYER                          │
│     (Entity, Event, Location, Relationship Extraction)       │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL CATALOG                        │
│            (Entities, Events, Locations, Documents)         │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                   INGESTION LAYER                            │
│            (Scanner, Chunkers, Indexer, Retriever)          │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                      PARSERS LAYER                          │
│              (Domain-specific artifact parsers)              │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                     FILESYSTEM                              │
│              (Source of truth - never modified)             │
└─────────────────────────────────────────────────────────────┘
```

## Core Abstractions

Librarian operates on these fundamental abstractions:

| Abstraction | Description | Example |
|-------------|-------------|---------|
| **Artifact** | A file in its native format | JPEG, JSON, Python file |
| **Document** | An indexed artifact with extracted metadata | Parsed file content |
| **Entity** | A named thing discovered in artifacts | Person, company, location |
| **Event** | A timestamped occurrence | Meeting, purchase, capture |
| **Location** | A geographic point or named place | City, GPS coordinates |
| **Evidence** | Assembled facts for a query | Entity list, timeline |

## Directory Structure

```
core/               # Core logic: librarian, query_planner, evidence_builder, timeline_builder
parsers/            # Artifact parsers: json, yaml, csv, image, etc.
extractors/         # Evidence extractors: entity, event, location
indexing/           # Indexing pipeline: scanner, chunker, indexer, retriever
storage/            # PostgreSQL backend for catalog persistence
registry/           # Parser registration system
graph/              # Dependency analysis (optional for code artifacts)
models/             # Data models and abstractions
tests/              # Test suite
samples/            # Sample artifacts for testing
docs/               # Documentation
```

## Supported Artifact Types

| Category | Formats | Parser | Workers |
|----------|--------|--------|---------|
| Images | JPEG, PNG, WebP, HEIC, GIF, BMP, TIFF | ImageParser | PhotoMetadataExtractor, OCRWorker, ObjectDetectionWorker |
| Structured | JSON, YAML, TOML, CSV | JsonParser, YamlParser, etc. | ContentExtractor |
| Code | Python | PythonParser | EntityExtractor, EmbeddingGenerator |
| Config | INI, XML | IniParser, XmlParser | EntityExtractor |
| Text | Plain text, Markdown | TextParser | EntityExtractor, EmbeddingGenerator |
| Future | PDF, DOC, audio, video, CAD | TBD | TBD |

### Image Support (Phase 1)

**ImageParser** provides lightweight ingestion:
- Validates image file
- Identifies MIME type
- Extracts dimensions
- Creates document record

**PhotoMetadataExtractor** worker provides enrichment:
- EXIF metadata extraction
- GPS coordinates
- Camera information
- Timestamps

## Query Pipeline

```
User Question
      ↓
Query Planner (regex-based intent detection)
      ↓
Evidence Builder (assembles evidence from catalog)
      ↓
Evidence Package → Agent
      ↓
Agent Reasoning → Answer
```

The purpose is NOT to answer questions directly. The purpose is to assemble evidence for an agent to reason over.

## Component Responsibilities

| Component | Directory | Responsibility |
|-----------|-----------|----------------|
| **Collection Watcher** | `ingestion/` | Monitors filesystem, detects file changes |
| **Parser Registry** | `registry/` | Routes files to appropriate parser |
| **Parsers** | `parsers/` | Creates artifact records (ingestion) |
| **Workers** | `workers/` | Enriches artifacts (extraction) |
| **Entity Extractor** | `extractors/` | Extracts named entities |
| **Event Extractor** | `extractors/` | Extracts timestamped events |
| **Location Extractor** | `extractors/` | Extracts locations and GPS |
| **Query Planner** | `core/` | Detects query intent using regex |
| **Evidence Builder** | `core/` | Assembles evidence packages |
| **Timeline Builder** | `core/` | Builds chronological timelines |
| **PostgreSQL Backend** | `storage/` | Persists catalog to database |

## Future Directions

- PDF and DOC parser support
- Audio/video transcription and metadata extraction
- CAD drawing metadata extraction
- Email thread parsing
- Spreadsheet data extraction
- Database schema extraction
- Telemetry data parsing

