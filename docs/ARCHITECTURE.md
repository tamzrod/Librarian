# ARCHITECTURE.md

## Architectural Layers

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
│                   INDEXING LAYER                            │
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

| Category | Types | Extracted Evidence |
|----------|-------|-------------------|
| Images | JPEG, PNG | GPS, timestamps, camera info, EXIF |
| Structured | JSON, YAML, TOML, CSV | Schema, values, relationships |
| Code | Python | Imports, classes, functions |
| Config | INI, XML | Key-value pairs, structure |
| Text | Plain text, Markdown | Entities via regex |
| Future | PDF, DOC, audio, video, CAD | TBD |

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
| **Scanner** | `indexing/` | Discovers files, computes hashes, tracks modifications |
| **Parser Registry** | `registry/` | Routes files to appropriate parser |
| **Parsers** | `parsers/` | Extract structured data from artifacts |
| **Indexer** | `indexing/` | Creates searchable index with metadata |
| **Retriever** | `indexing/` | Searches index for relevant documents |
| **Persistence** | `indexing/` | Saves/loads index to/from JSON |
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

