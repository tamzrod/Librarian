# Librarian

Librarian is an **evidence retrieval and context reconstruction engine** operating on bounded collections.

## What Librarian Is

- **Evidence Retrieval Engine**: Assembles evidence packages from indexed artifacts
- **Context Reconstruction System**: Rebuilds context from fragmented, distributed information
- **Knowledge Catalog**: Preserves artifacts in their native format while building a searchable catalog
- **Agentic Reasoning Support**: Enables AI agents to reason over evidence from bounded collections

Librarian is designed for **bounded collections** - a folder, a project, a knowledge base - and helps reconstruct what exists within those boundaries.

## What Librarian Is Not

- A code assistant or chatbot
- A document chatbot
- A traditional RAG system
- A vector database wrapper
- A code analysis tool
- A source code indexer

## The Vision

Traditional RAG:
```
Question → Chunk Retrieval → LLM
```

Librarian:
```
Bounded Collection → Artifact Ingestion → Evidence Extraction → Evidence Assembly → Agentic Reasoning
```

Librarian focuses on **digesting whatever exists inside a folder**, preserving artifacts in their native format, and extracting evidence to support agentic reasoning.

## Core Principles

1. **Filesystem is the source of truth** - Original files are never modified
2. **Artifacts are preserved** - Content stays in native format; only evidence is extracted
3. **Derived data is disposable** - Reindexing is always possible
4. **The catalog remains organized** - Even when the filesystem is not
5. **Evidence over summaries** - Assemble facts, let the agent reason

## Example User Questions

- "Where was I on January 1 2026?"
- "Give me the profile of Client ABC."
- "Show me all photos related to Project X."
- "What happened during February 2026?"
- "What is the drop wire length in this CAD project?"

## Supported Artifact Types

Librarian can ingest and extract evidence from:

| Category | Types |
|----------|-------|
| Text | Plain text, Markdown, logs |
| Structured | JSON, YAML, TOML, CSV, XML, INI |
| Images | JPEG, PNG (with GPS/EXIF extraction) |
| Documents | PDF, DOC |
| Code | Python, and extensible to others |
| Future | Audio, video, CAD, emails, spreadsheets, databases, telemetry |

## Quick Start

```python
from core.librarian import Librarian
from core.evidence_builder import build_evidence
from core.query_planner import plan_query

lib = Librarian()
lib.ingest('/path/to/bounded/collection')

# Plan the query
plan = plan_query("Where was I on January 1 2026?")

# Build evidence package
evidence = build_evidence(plan['question'], plan, lib.backend)
```

The library may live anywhere. Librarian only cares that it can reach the shelves.
