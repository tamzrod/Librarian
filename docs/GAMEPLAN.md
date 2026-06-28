## GAMEPLAN.md

### Development Phases

**Phase 1: Foundation**
- Filesystem scanner
- Metadata extraction
- Change detection
- Catalog persistence

**Phase 2: Ingestion**
- Document parsers (multi-format)
- Normalized internal document model
- Incremental indexing
- Domain-specific parser framework

**Phase 3: Discovery**
- Entity extraction
- Relationship extraction
- Dependency graph building
- Hotspot detection

**Phase 4: Retrieval**
- Keyword search
- Entity-based retrieval
- Relationship traversal
- Context assembly

**Phase 5: Reasoning**
- LLM enrichment
- Context package generation
- Multi-hop reasoning
- Background learning

**Phase 6: Integration**
- Assistant integration
- User feedback loops
- Knowledge refinement
- Continuous understanding

### Priority Order

1. Filesystem awareness
2. Domain-specific parsing
3. Entity discovery
4. Relationship mapping
5. Context retrieval
6. LLM reasoning

### Parser Domains (Planned)

| Domain | Entities | Relationships |
|--------|----------|---------------|
| Software | classes, functions, modules | imports, calls, extends |
| Business | customers, invoices, meetings | sent_to, scheduled_with |
| Personal Memory | locations, events, photos | visited, captured_at |
| Stories | characters, locations, events | interacts_with, located_at |
| Research | citations, authors, topics | cited_by, authored_by |