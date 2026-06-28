# VISION.md

## Why Librarian Exists

Librarian is an **evidence retrieval and context reconstruction engine** operating on bounded collections. It transforms unmanaged filesystems into **understandable, queryable evidence** without requiring users to reorganize their data.

### The Problem

Knowledge exists in scattered artifacts:
- Text documents, spreadsheets, emails
- Photos with GPS coordinates and timestamps
- Meeting notes, receipts, invoices
- Source code, CAD drawings, telemetry

Users need to find **what** happened, **where** it occurred, and **when** - not just remember **where** files are located.

### The Vision

**Traditional RAG:**
```
Question → Chunk Retrieval → LLM
```

**Librarian:**
```
Bounded Collection → Artifact Ingestion → Evidence Extraction → Evidence Assembly → Agentic Reasoning
```

Librarian focuses on:
1. **Digesting** whatever exists inside a folder
2. **Preserving** artifacts in their native format
3. **Extracting** evidence (entities, events, locations, timestamps)
4. **Building** a catalog of knowledge
5. **Supporting** agentic reasoning over evidence
6. **Supporting** memory reconstruction
7. **Supporting** future multimodal ingestion

### What Librarian Is Not

- A code assistant or chatbot
- A document chatbot
- A traditional RAG system
- A vector database wrapper
- A code analysis tool
- A source code indexer

### Core Principles

1. **Filesystem is the source of truth** - Original files are never modified
2. **Artifacts are preserved** - Content stays in native format; only evidence is extracted
3. **Derived data is disposable** - Reindexing is always possible
4. **The catalog remains organized** - Even when the filesystem is not
5. **Evidence over summaries** - Assemble facts, let the agent reason

### Example Questions

- "Where was I on January 1 2026?"
- "Give me the profile of Client ABC."
- "Show me all photos related to Project X."
- "What happened during February 2026?"
- "What is the drop wire length in this CAD project?"

The library may live anywhere. Librarian only cares that it can reach the shelves.