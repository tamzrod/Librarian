## VISION.md

### Why Librarian Exists

Librarian exists to transform unmanaged filesystems into **understandable, queryable knowledge** without requiring users to reorganize their data.

Librarian is a **context indexing engine**, **knowledge ingestion system**, **memory reconstruction system**, and **relationship discovery system**.

### The Problem

Knowledge is scattered across:
- Emails, documents, spreadsheets, and notes
- Calendar events, GPS history, and photos
- Meeting recordings, receipts, and invoices
- Research papers, citations, and references

Traditional systems force users to remember **where** information lives. Librarian helps users find **what** they need by understanding **how things relate**.

### The Vision

**Traditional RAG:**
```
Question → Chunk Retrieval → LLM
```

**Librarian:**
```
Question → Entity Discovery → Relationship Assembly → Context Package → LLM Reasoning
```

Librarian moves beyond simple chunk retrieval to:
1. Discover **entities** (people, places, concepts, events)
2. Map **relationships** between entities
3. Reconstruct **context** from fragmented information
4. Enable **reasoning** over distributed knowledge

### What Librarian Is Not

- A code analysis tool
- A source code indexer
- A static analysis platform
- A software-only RAG system

### Core Principles

1. **Filesystem is the source of truth** - Original files are never modified
2. **Parsers are domain-specific plugins** - Each domain has its own extraction logic
3. **Derived data is disposable** - Reindexing is always possible
4. **The catalog remains organized** - Even when the filesystem is not
5. **Knowledge becomes easier to access** - As the organization grows, not harder

### Example Questions

- "Give me the profile of client ABC."
- "Where was I on December 23 last year?"
- "Show all meetings related to Project Orion."
- "Which documents mention inverter failures?"
- "Summarize everything we know about customer XYZ."

The library may live anywhere. Librarian only cares that it can reach the shelves.