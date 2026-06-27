# Librarian Development Rules

## Philosophy

The filesystem is the source of truth.

Librarian never owns the books.
Librarian only owns the catalog.

Original files must never be modified.

Librarian may generate:
- metadata
- indexes
- embeddings
- summaries
- relationships
- retrieval context

Librarian must never become the authoritative source of information.

## Retrieval Model

Librarian scans all accessible folders and subfolders.

Knowledge is transformed into AI-friendly searchable representations.

When an AI assistant receives a question:

1. Librarian finds relevant knowledge.
2. Librarian assembles context.
3. Only relevant context is sent to the LLM.

Never attempt to load entire repositories into model context.

The library may contain millions of documents.

Retrieval is mandatory.

## Design Rules

- Filesystem is source of truth.
- Derived data is disposable.
- Reindexing must always be possible.
- Components must be replaceable.
- LLM providers must be replaceable.
- Embedding providers must be replaceable.
- Vector stores must be replaceable.
- Parsers must be replaceable.

## Mental Model

The library may live anywhere.

Librarian only cares that it can reach the shelves.