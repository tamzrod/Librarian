# GAMEPLAN.md

## Development Phases

**Phase 1: Foundation** ✅ COMPLETE
- Filesystem scanner
- Metadata extraction
- Change detection
- Catalog persistence (JSON)
- PostgreSQL integration

**Phase 2: Ingestion** ✅ COMPLETE
- Artifact parsers (multi-format: JSON, YAML, CSV, XML, INI, TOML, Python, Image)
- Normalized internal document model
- Incremental indexing
- Domain-specific parser framework

**Phase 3: Evidence Extraction** ✅ COMPLETE
- Entity extraction
- Event extraction with timestamps
- Location extraction (named + GPS)
- Dependency graph building
- Image EXIF/GPS parsing

**Phase 4: Evidence Assembly** ✅ COMPLETE
- Query planning (regex-based intent detection)
- Evidence building
- Timeline reconstruction
- Context assembly for agentic reasoning

**Phase 5: Multimodal Support** 🚧 IN PROGRESS
- [ ] PDF parser
- [ ] DOC parser
- [ ] Audio transcription
- [ ] Video metadata extraction
- [ ] CAD drawing parsing

**Phase 6: Advanced Integration** 📋 PLANNED
- [ ] Email thread parsing
- [ ] Spreadsheet extraction
- [ ] Database schema parsing
- [ ] Telemetry data handling
- [ ] Assistant/Agent integration

### Parser Domains (Implemented + Planned)

| Domain | Entities | Evidence Types | Status |
|--------|----------|----------------|--------|
| Software | classes, functions, modules | imports, structure | ✅ |
| Images | GPS, timestamps, camera | EXIF metadata | ✅ |
| Structured Data | schema, values | relationships | ✅ |
| Business | customers, invoices | timestamps, locations | 📋 |
| Personal Memory | locations, events | GPS, timestamps | 📋 |
| CAD Drawings | dimensions, components | measurements | 📋 |
| Email Threads | senders, recipients | timestamps | 📋 |

### Priority Order

1. Artifact ingestion from filesystem
2. Evidence extraction (entities, events, locations)
3. Query planning and evidence assembly
4. PostgreSQL catalog management
5. Multimodal support (PDF, audio, video, CAD)
6. Agent integration