# Librarian

Librarian is a filesystem-first RAG indexing backend for knowledge repositories.

As long as Librarian can access the folders, Librarian can access the books.

The filesystem remains the source of truth.

Librarian owns only metadata, indexes, embeddings, and retrieval context while leaving original files untouched.

Librarian is designed to support multiple document formats, multiple embedding providers, multiple vector databases, and multiple LLM providers through interchangeable interfaces.

Its responsibility is simple:

* discover knowledge
* organize knowledge
* track changes to knowledge
* retrieve knowledge efficiently

The library may live anywhere.

Librarian only cares that it can reach the shelves.
