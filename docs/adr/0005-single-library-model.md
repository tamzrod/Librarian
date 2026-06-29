# 0005-single-library-model.md

## Status
Accepted

## Context

Librarian serves as an evidence retrieval engine for bounded collections. The system must balance several design considerations:

- **Simplicity**: Avoid unnecessary complexity in deployment and operation
- **Automation**: Minimize user intervention in ongoing operations
- **Stability**: Provide a reliable contract for client integrations
- **Flexibility**: Support diverse client implementations

Early design discussions considered multi-collection models, manual ingestion triggers, and collection management UIs. This ADR documents the architectural decisions that led to a simpler, more automated approach.

## Decisions

### 1. Single Library Root

Librarian operates on a **single library root** at a time.

- One library root per deployment
- The library root is configured via Docker Compose volume mapping
- Example: `volumes: /home/user/documents:/library:ro`
- No runtime collection switching

### 2. Recursive File Scanning

Librarian recursively scans all files and subfolders within the library root.

- No user-defined scanning scope or folder selection
- Everything under the library root is indexed
- Exclusion patterns are configured globally (e.g., `.gitignore`, hidden files)

### 3. No Collection Management UI

There is no UI for managing collections.

- Collections are a deployment configuration concern, not a runtime one
- Configuration is done via environment variables or docker compose
- Runtime changes require redeployment

### 4. Automatic Ingestion

Users do not manually trigger ingestion.

- File changes are automatically detected and processed
- Uses filesystem watchers with polling fallback
- New and modified files are indexed automatically
- Deleted files are removed from the catalog

### 5. REST API as Public Interface

The REST API is the **public product interface**.

- All operations are exposed via API
- GUI clients communicate exclusively through the REST API
- The API is the stable, documented contract

### 6. Disposable GUI Clients

GUI implementations are intentionally **disposable and replaceable**.

- A new GUI can be built without affecting Librarian
- Mobile clients, web apps, CLI tools all use the same API
- The API decouples the core engine from presentation

### 7. API as Stable Contract

The API is the **stable contract**, not the GUI.

- GUI changes do not affect integrations
- API changes follow versioning with deprecation windows
- Clients depend on the API, not implementation details

### 8. Future Client Ecosystem

Future clients may include:

- Web GUI
- Desktop GUI (Electron, Tauri, etc.)
- CLI tool
- MCP (Model Context Protocol) integration
- Mobile apps
- Third-party integrations

## Rationale

### Why Single Library?

1. **Simplicity**: Reduces configuration complexity
2. **Predictability**: Users know exactly what is being indexed
3. **Deployment**: Maps cleanly to Docker volume mounts
4. **Performance**: Single scan scope is easier to optimize

### Why No Collection Management?

1. **Complexity**: Multi-collection adds significant complexity
2. **Use Case**: Most users have a single important folder to index
3. **Alternative**: Users can run multiple Librarian instances
4. **Configuration**: Environment-based configuration is sufficient

### Why Automatic Ingestion?

1. **User Experience**: "Set it and forget it" operation
2. **Reliability**: Eliminates human error in triggering ingestion
3. **Real-time**: Keeps index current without user intervention
4. **Simplicity**: No training required for ongoing operation

### Why API-First?

1. **Stability**: API contracts are easier to version and maintain
2. **Flexibility**: Any client can integrate
3. **Testing**: API is testable without GUI
4. **Documentation**: Clear contract for third-party developers

### Why Disposable GUI?

1. **Evolution**: GUI paradigms change frequently
2. **Specialization**: Different users want different interfaces
3. **Core Value**: The evidence engine is the valuable part
4. **Decoupling**: Core engine advances independently of UI

## Consequences

### Positive

1. Simple deployment model (single Docker container + volume)
2. No user training for ongoing operations
3. Stable API for integrations
4. Diverse client ecosystem possible
5. Easy to reason about system state

### Negative

1. Cannot switch libraries without redeployment
2. All files in library root are indexed (no selective scanning)
3. GUI clients are "throwaway" investments

## Alternatives Considered

### Multi-Collection Model

- **Rejected**: Adds complexity for marginal benefit
- Most users have one important folder to index
- Multiple instances is an acceptable workaround

### Manual Ingestion Trigger

- **Rejected**: Requires user training
- Automatic detection is more reliable
- "Magic" behavior is preferred for this use case

### GUI as Primary Interface

- **Rejected**: Limits integration possibilities
- GUI changes would break integrations
- Not all clients can run a GUI

## Implementation Notes

### Docker Compose Example

```yaml
services:
  librarian:
    image: librarian/engine:latest
    volumes:
      - /path/to/documents:/library:ro
    environment:
      - LIBRARY_ROOT=/library
      - DATABASE_URL=postgresql://...
```

### File Watching Strategy

1. Primary: Use filesystem watchers (inotify on Linux, FSEvents on macOS)
2. Fallback: Polling every 30 seconds when watchers unavailable
3. Deduplication: Avoid duplicate processing during rapid changes

### API Versioning

- Version prefix in URL: `/api/v1/`
- Deprecation headers on old versions
- 12-month sunset window for major versions
