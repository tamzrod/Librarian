# GOALS.md

## Project Goals

Librarian is an evidence retrieval and context reconstruction engine operating on bounded collections.

### Primary Objectives

1. **Evidence Retrieval**: Assemble evidence packages from indexed artifacts
2. **Context Reconstruction**: Rebuild context from fragmented, distributed information
3. **Knowledge Cataloging**: Preserve artifacts in native format while building catalog
4. **Agentic Support**: Enable AI agents to reason over bounded collections
5. **Multimodal Ingestion**: Support future audio, video, CAD, and other formats

### Success Criteria

- [x] Ingest artifacts from bounded collections
- [x] Extract entities automatically
- [x] Extract events with timestamps
- [x] Extract locations and GPS coordinates
- [x] Preserve filesystem as source of truth
- [x] Enable reindexing from scratch
- [x] Query planning with intent detection
- [x] Evidence assembly for agentic reasoning
- [ ] PDF and DOC parsing
- [ ] Audio/video transcription
- [ ] CAD metadata extraction
- [ ] Email thread parsing

### Current Capabilities

- ✅ Multi-format parsing (CSV, INI, JSON, TOML, XML, YAML, Python, Image)
- ✅ Document chunking
- ✅ Metadata extraction (hash, size, modified time)
- ✅ Keyword search
- ✅ Entity extraction
- ✅ Event extraction with timestamps
- ✅ Location extraction (named + GPS coordinates)
- ✅ Image EXIF/GPS extraction
- ✅ Query planning (regex-based intent detection)
- ✅ Evidence building for agentic reasoning
- ✅ Timeline reconstruction
- ✅ PostgreSQL catalog persistence

### Planned Capabilities

- [ ] PDF and DOC parser support
- [ ] Audio/video transcription and metadata
- [ ] CAD drawing metadata extraction
- [ ] Email thread parsing
- [ ] Spreadsheet data extraction
- [ ] Database schema extraction
- [ ] Telemetry data parsing

### Community Objectives

#### Community Ingestion Plugins

Enable community contributions for specialized artifact types:

- Plugin framework with standard interfaces
- Versioned plugin API for stability
- Sandboxed execution for security
- Plugin registry for discovery

#### Third-Party Parser Ecosystem

Support specialized parsers for domain-specific artifacts:

- CAD drawings (DWG, DXF, STEP)
- Email archives (PST, MBOX)
- Messaging data (WhatsApp, Signal)
- Telemetry data (drone logs, vehicle data)
- Enterprise formats (SAP, Salesforce exports)

#### Plugin Marketplace

Facilitate discovery and distribution of community parsers:

- Curated plugin directory
- Version compatibility checks
- Community ratings and reviews
- One-click installation
