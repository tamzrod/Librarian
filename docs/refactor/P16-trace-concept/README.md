# P16: Trace Concept Refactoring

## Executive Summary

Replace the separate **Timeline** and **Map** navigation paradigms with a single unified concept: **Trace**.

Trace represents the movement, progression, and spatial-temporal history of artifacts—unifying temporal sequence with spatial positioning into one cohesive investigation workspace.

## Motivation

### Current State

The current architecture treats **Timeline** and **Map** as two separate, orthogonal views:

```
┌─────────────┐     ┌─────────────┐
│  Timeline   │     │    Map      │
│  (temporal) │     │ (spatial)   │
└──────┬──────┘     └──────┬──────┘
       │                   │
       ▼                   ▼
   Sequence            Position
   History             Geography
```

**Problems:**
1. **Mental Discontinuity** — Users must mentally reconcile two separate views
2. **Synchronization Complexity** — Timeline ↔ Map state must remain synchronized
3. **Investigation Fragmentation** — Evidence spans both temporal and spatial dimensions
4. **Cognitive Overhead** — Context switching between views breaks investigative flow
5. **Terminology Ambiguity** — "Timeline" implies sequence; "Map" implies geography—but artifacts exist in both dimensions simultaneously

### Why "Trace"?

The term "Trace" is intentionally:
- **Neutral** — Avoids personal/emotional connotations ("Memories", "Journeys")
- **Professional** — Suitable for forensic, investigative, and enterprise contexts
- **Descriptive** — Captures the essence of following a path through time and space
- **Versatile** — Applies across domains (photos, forensics, inspections, OSINT)

Trace aligns with:
- "Trace evidence" in forensic science
- "Trace analysis" in signal processing
- "Trace route" in networking diagnostics
- "Trace file" in debugging/profiling

## Goals

### Primary Goals

1. **Unification** — Single conceptual model that encompasses temporal and spatial dimensions
2. **Investigation-First Design** — Workspace optimized for analysis, not browsing
3. **Playback & Reconstruction** — Support for replaying sequences, animating routes, scrubbing time
4. **Filter-Driven Discovery** — Node-RED inspired palette system for rapid filtering
5. **Scalable Visualization** — Support from single artifacts to millions of items

### Secondary Goals

1. **Backward Compatibility** — Timeline and Map coexist during migration
2. **Progressive Disclosure** — Simple by default, powerful on demand
3. **Domain Agnostic** — Works for photos, forensics, inspections, OSINT, archives
4. **Performance** — Handle large datasets with clustering, lazy loading, virtual scrolling

## Scope

### In Scope (Documentation Only)

- [x] README.md (this file)
- [x] VISION.md — What Trace is and what it enables
- [x] ARCHITECTURE.md — Unified data model
- [x] FILTERS.md — Filter palette system design
- [x] DATA_MODEL.md — Schema audit and gap analysis
- [x] MIGRATION_PLAN.md — Phased rollout strategy
- [x] UI_LAYOUT.md — Workspace layout specifications

### Out of Scope

- ❌ Code implementation
- ❌ Frontend route changes
- ❌ Component renaming
- ❌ Pull requests
- ❌ Pushing changes

## The Transformation

```
Timeline + Map
       ↓
     Trace
```

| Aspect | Before | After |
|--------|--------|-------|
| **Navigation** | Timeline / Map tabs | Single Trace workspace |
| **Filtering** | Scattered controls | Unified palette |
| **Visualization** | Split views | Integrated canvas |
| **Playback** | Manual navigation | Transport controls |
| **Mental Model** | Two paradigms | One concept |

## Quick Links

- [VISION.md](./VISION.md) — Define Trace as Spatial + Temporal Intelligence
- [ARCHITECTURE.md](./ARCHITECTURE.md) — Document the unified Trace model
- [FILTERS.md](./FILTERS.md) — Node-RED inspired filter palette system
- [DATA_MODEL.md](./DATA_MODEL.md) — Schema audit and gap analysis
- [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) — Phased migration strategy
- [UI_LAYOUT.md](./UI_LAYOUT.md) — Unified Trace workspace design

## Status

**Phase:** Documentation Complete  
**Next:** Stakeholder Review → Architecture Review → Implementation Planning

---

*This is a documentation-only refactoring proposal. No code changes have been made.*