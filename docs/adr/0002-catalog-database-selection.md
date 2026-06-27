# 0002-catalog-database-selection.md

## Status
Accepted

## Context
Librarian is a filesystem-first RAG indexing backend for shared folders and enterprise knowledge repositories. The decision to select a catalog database involves choosing a system that can efficiently store and manage derived information such as metadata, hashes, indexing state, folder hierarchy, summaries, chunk information, and embedding references.

## Decision
MariaDB will initially be used as the catalog database.

## Rationale
1. **Performance**: MariaDB offers high performance and scalability, making it suitable for handling large volumes of metadata.
2. **Reliability**: It is a robust and reliable database system with strong community support.
3. **Compatibility**: MariaDB is compatible with many existing tools and libraries, simplifying integration.
4. **Cost-Effectiveness**: MariaDB provides a cost-effective solution compared to other enterprise-level databases.

## Alternatives Considered
1. **SQLite**: Lightweight and easy to set up, but may not scale well for large datasets.
2. **PostgreSQL**: Offers advanced features like JSON support and full-text search, but with higher complexity.
3. **Storing metadata directly in the vector database**: This approach would couple catalog storage with vector storage, making future replacements more challenging.
4. **Filesystem-only metadata storage**: While simple, it lacks structured querying capabilities and can become inefficient as data grows.

## Consequences
1. **Initial Implementation**: Using MariaDB will allow for a robust initial implementation that meets current requirements.
2. **Future Flexibility**: The decision to use MariaDB does not preclude future replacements or upgrades, preserving flexibility in the system architecture.

## Future Re-evaluation Criteria
1. **Performance Bottlenecks**: If performance issues arise with MariaDB, it may be necessary to re-evaluate and consider more scalable solutions.
2. **Feature Requirements**: As new features are added, the database system may need to support additional functionalities that could drive a change in selection.
3. **Cost Considerations**: Changes in operational costs or licensing models might influence future decisions.

