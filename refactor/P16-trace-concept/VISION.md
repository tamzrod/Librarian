# VISION.md — Trace: Spatial + Temporal Intelligence

## Vision Statement

> **Trace** is a unified workspace that reveals the spatial-temporal narrative of artifacts—where they went, when they were there, and what connected them.

Trace transforms raw artifact collections into navigable, filterable, replayable histories. It is the investigation workspace for understanding not just *what* happened, but *where*, *when*, and *how* it all connects.

## Core Definition

### Trace = Spatial + Temporal Intelligence

Trace is the convergence of two intelligence dimensions:

```
┌─────────────────────────────────────────────────────────┐
│                      TRACE                              │
│                                                         │
│    SPATIAL ─────────────┬────────────── TEMPORAL       │
│         │               │                │             │
│         ▼               ▼                ▼             │
│    ┌─────────┐    ┌──────────┐    ┌──────────┐       │
│    │  Where  │    │  TRACE   │    │  When    │       │
│    │         │◄──►│  MODEL   │◄──►│          │       │
│    │ Location│    │          │    │ Sequence │       │
│    └─────────┘    └──────────┘    └──────────┘       │
│                                                         │
│    Position ◄────────────┼────────────► Timeline     │
│    Geography             │            History         │
│                          │                            │
│                          ▼                            │
│              ┌─────────────────────┐                  │
│              │  INVESTIGATION       │                  │
│              │  • Playback          │                  │
│              │  • Reconstruction     │                  │
│              │  • Navigation         │                  │
│              │  • Clustering         │                  │
│              │  • Route Animation    │                  │
│              └─────────────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

## Trace Capabilities

Trace enables six core investigative operations:

### 1. Playback

Replay artifact sequences as a continuous narrative.

**Use Cases:**
- Walk through a day's photos chronologically
- Reconstruct an incident timeline frame by frame
- Review a field inspection from start to finish

**Controls:**
- Play / Pause / Stop
- Speed: 1x, 2x, 4x, 8x, 16x, 32x
- Frame-by-frame stepping
- Jump to date/time
- Scrub through history

### 2. Filtering

Drill into specific subsets using a powerful, visual filter palette.

**Use Cases:**
- Show only photos from a specific device
- Filter by GPS location radius
- Include only artifacts with certain tags
- Show items from a date range

**Filter Categories:**
- Device (HONOR BRP-NX1, Xiaomi, iPhone, DJI Drone, Canon DSLR)
- Source (GPS EXIF, OCR, Manual Tag, Semantic Location)
- Artifact Type (Images, Video, Documents, Audio)
- Collections (Camera Roll, Evidence, Project Alpha)
- Time Range (Year, Month, Day, Custom)
- Location (Map bounds, Radius, Region)
- Tags (Custom labels, Entity names)
- Relationships (Connected artifacts, Network graphs)

### 3. Reconstruction

Build complete narratives from fragmentary evidence.

**Use Cases:**
- Reconstruct a crime scene from scattered photos
- Piece together a project timeline from documents
- Restore a day's events from multiple sources

**Features:**
- Automatic event clustering
- Gap detection and visualization
- Relationship mapping
- Narrative ordering

### 4. Investigation

Deep-dive into connections, patterns, and anomalies.

**Use Cases:**
- Trace a person's movement through an area
- Identify suspicious patterns in asset locations
- Correlate evidence across multiple sources
- Find connections between seemingly unrelated artifacts

**Investigation Tools:**
- Relationship graph visualization
- Anomaly highlighting
- Pattern detection
- Cross-reference linking

### 5. Navigation

Explore spatial-temporal data with fluid, intuitive movement.

**Use Cases:**
- Pan and zoom through a timeline spatially
- Jump between significant events
- Fly through a geographic route
- Explore nested collections

**Navigation Modes:**
- Geographic (map-centric)
- Chronological (time-centric)
- Hierarchical (collection-centric)
- Network (relationship-centric)

### 6. Clustering

Group artifacts intelligently to manage scale.

**Use Cases:**
- Cluster photos by location (geoclustering)
- Group by time proximity (timeclustering)
- Combine by semantic similarity (AI clustering)
- Aggregate by collection/folder

**Cluster Types:**
- Spatial clusters (location-based)
- Temporal clusters (time-based)
- Semantic clusters (content-based)
- Mixed clusters (multi-dimensional)

### 7. Replay

Animated visualization of artifact sequences.

**Use Cases:**
- Animate a vehicle's route on the map
- Show a day's worth of photos as a slideshow
- Visualize network traffic over time
- Playback an investigation sequence

**Replay Features:**
- Route animation on map
- Sequential highlight on timeline
- Smooth transitions
- Configurable duration
- Trail persistence (show where you've been)

## Trace vs. Alternatives

### Why Not "Timeline"?

Timeline implies:
- Linear sequence only
- Time as the primary dimension
- Spatial data as secondary annotation
- Simple "what happened when" queries

Trace supports:
- Non-linear exploration
- Time AND space as co-equal dimensions
- Spatial data as first-class citizen
- Complex "what happened, where, and how it connects" queries

### Why Not "Map"?

Map implies:
- Geographic primacy
- Space as the primary dimension
- Time as secondary annotation
- Simple "where" queries

Trace supports:
- Non-geographic contexts (internal networks, abstract spaces)
- Space as one of multiple dimensions
- Time as first-class citizen
- Complex spatial-temporal investigations

### Why Not "Memories" or "Journeys"?

Personal terms:
- Imply emotional/consumer context
- Don't fit forensic/investigative use cases
- Feel inappropriate for professional/enterprise use
- Limit the conceptual scope

Trace is:
- Domain-agnostic
- Professional and neutral
- Suitable for any artifact type
- Investigation-ready

## Design Principles

### 1. Spatial-Temporal Unity

Time and space are not separate views—they are two facets of the same Trace. Every artifact has both temporal and spatial properties, and Trace treats them as unified.

### 2. Investigation-First

Trace is built for people who need to understand, reconstruct, and investigate—not just browse. Every feature serves the investigative workflow.

### 3. Filter Everything

Filtering is the primary interaction model. Users should be able to narrow down millions of artifacts to the relevant few in seconds.

### 4. Playback by Default

The default view should be a playable sequence, not a static map or list. Users can scrub, animate, and replay.

### 5. Scale Gracefully

From 10 artifacts to 10 million, Trace should remain responsive and usable through intelligent clustering and virtualization.

### 6. Context Preservation

Every view should maintain awareness of the broader context. Users should never lose sight of what they're investigating.

## Success Metrics

Trace is successful when:

1. **Time to Insight** — Users find relevant patterns 50% faster than with separate Timeline/Map
2. **Investigation Coverage** — Users explore 3x more artifacts in the same session
3. **Conceptual Clarity** — New users understand Trace without explanation
4. **Zero Mental Switching** — Users never need to "switch views" to see related information
5. **Filter Adoption** — 80% of sessions involve active filter usage

## Future Vision

### Phase 1: Unified Workspace

Single Trace view that combines timeline and map functionality.

### Phase 2: Advanced Playback

Full animation, route tracing, timeline scrubbing, speed control.

### Phase 3: Intelligent Clustering

AI-powered clustering that groups artifacts by semantic similarity.

### Phase 4: Collaboration

Share traces, annotate findings, collaborate on investigations.

### Phase 5: Export & Reporting

Generate investigation reports, export evidence packages, create presentations.

---

*Trace: Where every artifact tells a story through time and space.*