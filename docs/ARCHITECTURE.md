# ARCHITECTURE.md

## High-Level System Architecture

Librarian is designed as a filesystem-first RAG indexing backend. The system consists of several key components, each with specific responsibilities:

1. **Filesystem Watcher**: Monitors changes in shared folders and enterprise knowledge repositories.
2. **Metadata Extractor**: Extracts metadata from files and stores it in the catalog database.
3. **Indexing Engine**: Manages the indexing process for derived information such as summaries, chunk information, and embedding references.
4. **Catalog Database**: Stores metadata, hashes, indexing state, folder hierarchy, summaries, chunk information, and embedding references.
5. **Vector Database**: Handles vector storage and retrieval operations independently of the catalog database.

## Component Responsibilities

- **Filesystem Watcher**:
  - Detects file additions, deletions, and modifications in monitored directories.
  - Triggers metadata extraction and indexing processes as needed.

- **Metadata Extractor**:
  - Reads file content and extracts relevant metadata.
  - Stores extracted metadata in the catalog database.

- **Indexing Engine**:
  - Processes files to generate summaries, chunk information, and embeddings.
  - Updates the catalog database with derived information.

- **Catalog Database**:
  - Manages structured storage of metadata and indexing state.
  - Provides efficient querying capabilities for metadata retrieval.

- **Vector Database**:
  - Stores vector representations of file content.
  - Supports similarity searches and other vector-based operations.

