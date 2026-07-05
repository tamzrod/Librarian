# Operation Plugin Foundation

**Status:** Implementation Phase  
**Objective:** Establish minimum runtime foundation for multi-plugin support  
**Predecessor:** [Operation Plugin Ready](../operation-plugin-ready/)

---

## Purpose

Operation Plugin Foundation closes the architectural gaps identified in Operation Plugin Ready. It establishes the smallest set of primitives required so future plugins can coexist safely.

## Context

Operation Plugin Ready completed a full architecture audit and produced an implementation roadmap. It identified:

- **✅ Already Supported:** Failure isolation, enable/disable controls, derived artifact storage, schema evolution
- **⚠️ Partial:** Provenance, versioning, reprocessing, multi-engine readiness
- **❌ Unsupported:** Plugin namespacing

## Foundation Requirements

This operation establishes support for:

| Requirement | Description |
|------------|-------------|
| **Plugin Identity** | Every observation attributable to plugin_name, engine_name, plugin_version |
| **Provenance** | Every observation answers who, which engine, which version, when |
| **Namespacing** | Clear ownership boundaries (e.g., exif.gps, yolo.object) |
| **Reprocessing Boundaries** | Ability to reprocess one plugin without affecting others |
| **Multi-Engine Readiness** | Architecture allows YOLO, Grounding DINO, OWL-ViT to coexist |

## Design Principles

```
Artifacts are the source of truth.
Plugins are observers.
Plugins produce observations.
Plugins may overlap.
Plugins may disagree.
Librarian stores observations.
Librarian does not determine canonical truth.
Consumers assign meaning.
```

## Non-Goals

This operation does NOT implement:
- Object Detection
- OCR
- Captioning
- Audio Transcription
- Video Analysis
- Plugin Marketplace
- Hot Loading
- Dynamic Plugins
- Remote Plugins
- Plugin RPC
- Distributed Execution
- Sandboxing

The goal is to support Plugin #2, not Plugin #2000.

## Deliverables

### Documentation

| Document | Description |
|----------|-------------|
| [plugin-identity.md](./plugin-identity.md) | Plugin identity requirements |
| [provenance-model.md](./provenance-model.md) | Provenance tracking model |
| [namespacing-strategy.md](./namespacing-strategy.md) | Namespace conventions |
| [reprocessing-boundaries.md](./reprocessing-boundaries.md) | Reprocessing isolation |
| [multi-engine-readiness.md](./multi-engine-readiness.md) | Engine coexistence |
| [implementation-options.md](./implementation-options.md) | Implementation approaches |
| [risk-analysis.md](./risk-analysis.md) | Risk assessment |
| [migration-plan.md](./migration-plan.md) | Database changes |
| [success-criteria.md](./success-criteria.md) | Success metrics |

### Implementation

| Component | Change |
|----------|--------|
| `registry/plugin_registry.py` | Add plugin identity fields |
| Database | Add provenance columns |
| Workers | Include provenance in observations |
| Tests | Verify foundation works |

## Implementation Approach

**Prefer:**
- Small changes
- Incremental evolution
- Low blast radius

**Avoid:**
- Large rewrites
- Schema redesigns
- Framework creation

## Success Criteria

At completion, we should be able to answer YES to:

> If tomorrow we add:
> - Object Detection
> - OCR
> - Captioning
> - PDF Extraction
> - Audio Transcription
>
> do we know:
> - where observations belong? ✅
> - how provenance works? ✅
> - how versions work? ✅
> - how reprocessing works? ✅
> - how multiple engines coexist? ✅

## Related Documentation

- [Operation Plugin Ready](../operation-plugin-ready/) - Audit and planning
- [Plugin Philosophy](../operation-plugin-ready/plugin-philosophy.md) - Core principles
- [Plugin Contract](../operation-plugin-ready/plugin-contract.md) - Interface definition
- [Multi-Engine Strategy](../operation-plugin-ready/multi-engine-strategy.md) - Engine support

## Stop Condition

Implementation stops when:
- All foundation requirements implemented
- Tests pass
- Documentation complete

Implementation does NOT begin:
- Object Detection
- OCR
- Captioning

Those belong to future operations.
