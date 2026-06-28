# Librarian

Librarian is a **context indexing engine**, **knowledge ingestion system**, **memory reconstruction system**, and **relationship discovery system** for personal and organizational knowledge.

## What Librarian Is

- **Context Indexing Engine**: Transforms unstructured files into organized, searchable knowledge
- **Knowledge Ingestion System**: Ingests documents across multiple formats and domains
- **Memory Reconstruction System**: Rebuilds context from fragmented, distributed information
- **Relationship Discovery System**: Uncovers connections between entities across documents

## What Librarian Is Not

- A code analysis tool
- A source code indexer
- A static analysis platform
- A software-only RAG system

Librarian supports any domain: software, business, personal memory, stories, research, or any other knowledge domain.

## The Vision

Traditional RAG:
```
Question → Chunk Retrieval → LLM
```

Librarian:
```
Question → Entity Discovery → Relationship Assembly → Context Package → LLM Reasoning
```

Librarian moves beyond simple chunk retrieval to understand **what** exists (entities) and **how things relate** (relationships), enabling deeper reasoning over distributed knowledge.

## Core Principles

1. **Filesystem is the source of truth** - Original files are never modified
2. **Parsers are domain-specific plugins** - Each domain has its own extraction logic
3. **Derived data is disposable** - Reindexing is always possible
4. **The catalog remains organized** - Even when the filesystem is not

## Example User Questions

- "Give me the profile of client ABC."
- "Where was I on December 23 last year?"
- "Show all meetings related to Project Orion."
- "Which documents mention inverter failures?"
- "Summarize everything we know about customer XYZ."

## Quick Start

```python
from librarian import Librarian

lib = Librarian()
lib.ingest('/path/to/knowledge/base')
results = lib.search("inverter failures")
```

The library may live anywhere. Librarian only cares that it can reach the shelves.
