# Architecture Impact — Operation Playback

## Overview

This document analyzes the impact of Operation Playback on the existing codebase architecture. It identifies affected components, required changes, and integration points.

---

## Component Impact Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARCHITECTURE IMPACT OVERVIEW                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DASHBOARD (Frontend)                                                        │
│  ├── src/pages/TraceView.tsx          ████████████████████ HIGH IMPACT      │
│  ├── src/components/FilterPalette.tsx  ██████████          MEDIUM IMPACT    │
│  ├── src/components/FilmStrip.tsx      ████████████████████ HIGH IMPACT     │
│  ├── src/components/MapCanvas.tsx      ████████████████     HIGH IMPACT      │
│  ├── src/components/EventStream.tsx    ████████████████     REMOVED         │
│  ├── src/components/Layout.tsx         ████                 LOW IMPACT       │
│  └── src/services/api.ts               ██████████          MEDIUM IMPACT    │
│                                                                             │
│  API (Backend)                                                              │
│  ├── api/routes/trace.py              ██████████          MEDIUM IMPACT     │
│  ├── api/app_state.py                 ████                 LOW IMPACT       │
│  └── api/dependencies.py             ██                   MINIMAL IMPACT   │
│                                                                             │
│  STORAGE (Database)                                                          │
│  └── Postgres schema                 ██                   MINIMAL IMPACT     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Frontend Architecture Impact

### 1. TraceView.tsx — HIGH IMPACT

**Current Responsibilities:**
- Manages filter state
- Manages view mode (map/timeline/grid)
- Coordinates selection between components
- Handles URL parameter parsing

**Operation Playback Additions:**

```typescript
// New state for playback
interface PlaybackState {
  mode: 'stopped' | 'playing' | 'paused'
  direction: 'forward' | 'reverse'
  speed: number // 0.5, 1, 2, 4, 8, 16
  currentIndex: number
  currentTimestamp: string | null
}

// New synchronization state
interface SyncState {
  playheadTimestamp: string | null
  isSyncing: boolean // prevents feedback loops
}
```

**Required Changes:**
1. Add playback state management
2. Add playback control handlers
3. Add animation frame management for playback
4. Add keyboard event handlers
5. Add timeline component integration
6. Remove EventStream integration
7. Adjust layout for timeline x-axis

**API Changes Required:**
- `getTraceData()` → May need pagination enhancement
- New endpoint for timeline bucket summary (for 100k+ support)

### 2. FilterPalette.tsx — MEDIUM IMPACT

**Current State:**
- Filter groups: devices, sources, types, collections, years, timeRange
- Years filter is discrete checkboxes

**Operation Playback Changes:**

| Change | Type | Rationale |
|--------|------|-----------|
| Remove `years` filter group | REMOVAL | Replaced by continuous timeline |
| Enhance `timeRange` group | MODIFICATION | Timeline provides visual time selection |
| Add timeline position filter | ADDITION | Jump to specific date range |

**FilterState Interface Changes:**

```typescript
// BEFORE
interface FilterState {
  cameras: string[]
  collections: string[]
  years: string[]        // ← REMOVE
  sources: string[]
  startDate: string | null
  endDate: string | null
  includeUnknownDevice: boolean
}

// AFTER
interface FilterState {
  cameras: string[]
  collections: string[]
  // years removed
  sources: string[]
  startDate: string | null
  endDate: string | null
  includeUnknownDevice: boolean
  timelinePosition?: string | null // NEW: current playhead position
}
```

### 3. FilmStrip.tsx — HIGH IMPACT

**Current State:**
- Fixed height (~120px)
- Horizontal scrolling
- Thumbnail size: ~80px
- Basic hover state

**Operation Playback Changes:**

| Change | Type | Rationale |
|--------|------|-----------|
| Increase default height | MODIFICATION | Primary content area |
| Larger thumbnails (~150px) | MODIFICATION | Better visibility |
| Add hover preview popup | ADDITION | Key feature |
| Add virtualization | ADDITION | 100k+ support |
| Track selected index | MODIFICATION | Playback requires index |
| Auto-scroll to playhead | ADDITION | Synchronization |

**Component Interface Changes:**

```typescript
interface FilmStripProps {
  filters: FilterState
  onThumbnailClick?: (item: TraceEventItem) => void
  selectedThumbnailId?: number
  scrollToThumbnailId?: number
  // NEW PROPS
  isPlaybackMode?: boolean
  currentPlaybackIndex?: number
  onHoverPreview?: (item: TraceEventItem | null) => void
}
```

**Virtualization Implementation:**
- Use `react-window` or `@tanstack/react-virtual`
- Render only visible frames + buffer
- Maintain scroll position during playback

### 4. MapCanvas.tsx — HIGH IMPACT

**Current State:**
- Displays markers for GPS photos
- Basic clustering
- Popup on marker click
- Centers on marker on `centerOnMarkerId`

**Operation Playback Changes:**

| Change | Type | Rationale |
|--------|------|-----------|
| Follow playhead position | MODIFICATION | Synchronization |
| Add marker hover preview | ADDITION | Key feature |
| Enhanced clustering | MODIFICATION | 100k+ support |
| Animate marker transitions | ADDITION | Smooth playback |
| Remove event stream integration | REMOVAL | Timeline replaces |

**Current Props:**
```typescript
interface MapCanvasProps {
  filters: FilterState
  onMarkerClick?: (marker: TraceMapMarker) => void
  selectedMarkerId?: number
  centerOnMarkerId?: number
}
```

**New Props:**
```typescript
interface MapCanvasProps {
  filters: FilterState
  onMarkerClick?: (marker: TraceMapMarker) => void
  selectedMarkerId?: number
  centerOnMarkerId?: number
  // NEW: Playback integration
  isPlaybackMode?: boolean
  currentMarkerId?: number | null
  onMarkerHover?: (marker: TraceMapMarker | null) => void
}
```

### 5. EventStream.tsx — REMOVED

**Status:** Component will be removed entirely.

**Replacement:** Timeline X-axis component (new)

**Removal Checklist:**
- [ ] Remove import from TraceView.tsx
- [ ] Remove component file
- [ ] Remove CSS file
- [ ] Remove from routing
- [ ] Update TypeScript types
- [ ] Migrate any unique functionality

### 6. Layout.tsx — LOW IMPACT

**Current State:** Fixed sidebar + main content layout

**Operation Playback Changes:**
- Layout may need adjustment for timeline x-axis
- Bottom area will host timeline instead of event stream
- No structural changes required

### 7. api.ts Service — MEDIUM IMPACT

**Current State:**
- `getTraceData()` — Returns markers and events
- `getTraceFilters()` — Returns filter groups
- `getTraceThumbnailUrl()` — Returns thumbnail URL

**Required Changes:**

```typescript
// Existing
interface TraceDataParams {
  cameras?: string
  collections?: string
  years?: string      // ← Deprecate
  sources?: string
  startDate?: string
  endDate?: string
  includeUnknownDevice?: boolean
  limit?: number
}

// Enhancement: Cursor-based pagination
interface TraceDataParams {
  // ... existing
  cursor?: string      // NEW: For large collections
  limit?: number
}

// NEW: Timeline summary endpoint
interface TimelineSummaryResponse {
  buckets: TimelineBucket[]
  totalCount: number
  minDate: string
  maxDate: string
}

interface TimelineBucket {
  date: string
  count: number
  thumbnailUrl?: string
}
```

---

## Backend Architecture Impact

### 1. api/routes/trace.py — MEDIUM IMPACT

**Current Endpoints:**
- `GET /api/trace` — Returns markers, events, stats, filters
- `GET /api/trace/filters` — Returns filter groups
- `GET /api/trace/thumbnail/{path}` — Serves thumbnail

**Required Changes:**

| Endpoint | Change | Rationale |
|----------|--------|-----------|
| `/api/trace` | Add cursor pagination | 100k+ support |
| `/api/trace` | Remove `years` parameter | Replaced by date range |
| `/api/trace/timeline` | NEW endpoint | Bucket summary for timeline |
| `/api/trace/range` | NEW endpoint | Items in specific time range |

**New Endpoints:**

```python
# Timeline bucket summary
@app.get("/api/trace/timeline")
async def get_timeline_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    bucket_size: str = "auto"  # auto, day, week, month, year
) -> TimelineSummaryResponse:
    """
    Returns aggregated timeline data for visualization.
    """
    pass

# Items in time range (for playback)
@app.get("/api/trace/range")
async def get_trace_range(
    start_timestamp: str,
    end_timestamp: str,
    limit: int = 1000,
    cursor: Optional[str] = None
) -> TraceRangeResponse:
    """
    Returns items within a specific time range.
    """
    pass
```

### 2. api/app_state.py — LOW IMPACT

**Current State:** Global app state including database connections

**Changes:** Minimal, primarily documentation updates if state management changes

### 3. Storage/Postgres Backend — MINIMAL IMPACT

**Current Schema:**
- `documents` table with timestamps
- `photo_metadata` table with GPS coordinates
- `locations` table with semantic locations

**Required Changes:**
- Likely no schema changes
- May need index on `timestamp` for range queries
- Verify existing indexes support timeline queries

---

## State Management Architecture

### Current State Flow

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│ FilterPalette│────▶│    TraceView     │────▶│  MapCanvas  │
└─────────────┘     │   (useState)     │     └─────────────┘
                    │                  │
                    │  filters: {}      │     ┌─────────────┐
                    │  selectedId      │────▶│  FilmStrip  │
                    │  viewMode        │     └─────────────┘
                    │                  │
                    │                  │     ┌─────────────┐
                    │  scrollToId      │────▶│ EventStream │
                    │  centerOnId       │     └─────────────┘
                    └──────────────────┘
```

### Operation Playback State Flow

```
┌─────────────┐     ┌─────────────────────────────────────┐
│ FilterPalette│────▶│              TraceView              │
└─────────────┘     │            (useState + Context)       │
                    │                                         │
                    │  playback: {                            │
                    │    mode: 'stopped'|'playing'|'paused', │
                    │    direction: 'forward'|'reverse',     │
                    │    speed: 1,                            │
                    │    currentIndex: 0,                    │
                    │    currentTimestamp: null               │
                    │  }                                     │
                    │                                         │
                    │  sync: {                                │
                    │    playhead: timestamp,                 │
                    │    isSyncing: false                    │
                    │  }                                     │
                    └───────────────────────────────────────┬┘
                                │            │            │
                                ▼            ▼            ▼
                    ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
                    │ TimelineAxis│ │  MapCanvas  │ │  FilmStrip   │
                    │  (NEW)      │ │             │ │              │
                    └─────────────┘ └─────────────┘ └──────────────┘
```

---

## Data Flow Architecture

### Playback Data Flow

```
1. User presses Play
       │
       ▼
2. TraceView starts animation frame loop
       │
       ▼
3. For each frame (at 30fps / speed):
   │
   ├── Calculate next index based on direction
   │
   ├── If within bounds:
   │     │
   │     ├── Update playback state (currentIndex)
   │     │
   │     ├── Trigger sync updates:
   │     │     ├── MapCanvas: centerOnMarkerId
   │     │     ├── FilmStrip: scrollToThumbnailId
   │     │     └── TimelineAxis: playhead position
   │     │
   │     └── Request thumbnail preloading
   │
   └── If at boundary:
         │
         └── Stop playback
```

### Synchronization Protocol

To prevent feedback loops:

```typescript
interface SyncProtocol {
  // When updating from playback:
  // 1. Set isSyncing = true
  // 2. Update all components
  // 3. Set isSyncing = false
  
  // When responding to user interaction:
  // If isSyncing, ignore sync-triggered updates
  // Otherwise, update playback state
}
```

---

## Performance Architecture

### 100k+ Image Support Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERFORMANCE LAYERS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LAYER 1: Initial Load                                          │
│  ├── Show skeleton immediately                                  │
│  ├── Load filter metadata (fast, small)                         │
│  ├── Load timeline buckets (aggregated)                         │
│  └── Load first page of items (100-200)                        │
│                                                                 │
│  LAYER 2: Progressive Enhancement                               │
│  ├── Virtual scroll filmstrip (only render visible)             │
│  ├── Cluster map markers (max 500 clusters)                     │
│  ├── Preload adjacent thumbnails                                │
│  └── Background load remaining items                            │
│                                                                 │
│  LAYER 3: Playback Optimization                                 │
│  ├── Pre-calculate playback sequence                            │
│  ├── Preload thumbnails ahead of playhead                       │
│  ├── Use requestAnimationFrame for smooth playback              │
│  └── Throttle map updates during fast playback                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Virtualization Strategy

**FilmStrip:**
```typescript
// Use react-window FixedSizeList
<FixedSizeList
  width="100%"
  height={240}
  itemCount={items.length}
  itemSize={160}  // thumbnail width + gap
  layout="horizontal"
>
  {({ index, style }) => (
    <FilmStripFrame
      item={items[index]}
      style={style}
    />
  )}
</FixedSizeList>
```

**Timeline:**
```typescript
// Bucket-based rendering
interface TimelineBucket {
  date: Date
  count: number
  thumbnailUrl?: string
}

// At far zoom: large buckets (months/years)
// At close zoom: small buckets (days/hours)
```

---

## API Contract Changes

### Current Contract

```typescript
// GET /api/trace
interface TraceDataResponse {
  markers: TraceMapMarker[]
  events: TraceEventItem[]
  stats: {
    total: number
    with_gps: number
    unique_cameras: number
  }
  filters?: TraceFilterResponse  // If filters also fetched
}

// NEW: GET /api/trace with cursor pagination
interface TraceDataResponse {
  markers: TraceMapMarker[]
  events: TraceEventItem[]
  stats: TraceStats
  pagination?: {
    cursor: string | null
    has_more: boolean
    total_count: number
  }
}

// NEW: GET /api/trace/timeline
interface TimelineSummaryResponse {
  buckets: TimelineBucket[]
  total_count: number
  min_date: string
  max_date: string
}
```

---

## Type Changes

### TypeScript Type Updates

```typescript
// src/types/api.ts

// MODIFIED: TraceDataParams
interface TraceDataParams {
  cameras?: string
  collections?: string
  years?: string  // DEPRECATED - will be ignored
  sources?: string
  startDate?: string
  endDate?: string
  includeUnknownDevice?: boolean
  limit?: number
  cursor?: string  // NEW
}

// NEW: Playback types
interface PlaybackState {
  mode: 'stopped' | 'playing' | 'paused'
  direction: 'forward' | 'reverse'
  speed: number
  currentIndex: number
  currentItem: TraceEventItem | null
}

// NEW: Timeline types
interface TimelineBucket {
  id: string
  date: string
  count: number
  thumbnailUrl?: string
}

interface TimelineSummary {
  buckets: TimelineBucket[]
  totalCount: number
  minDate: string
  maxDate: string
}
```

---

## Testing Architecture

### Unit Tests Required

| Component | Tests |
|-----------|-------|
| TraceView | Playback state transitions, keyboard handlers, sync logic |
| FilmStrip | Virtualization, scroll behavior, hover preview |
| MapCanvas | Clustering, hover preview, sync updates |
| FilterPalette | Years filter removal, timeline filter integration |

### Integration Tests Required

| Scenario | Description |
|----------|-------------|
| Playback flow | Start → Play → Pause → Stop cycle |
| Sync test | Click filmstrip → Map updates |
| Large collection | Load 100k items, verify performance |
| Filter + Playback | Filter → Play filtered items |
| Keyboard navigation | All shortcuts work correctly |

---

## Dependency Compatibility

### External Dependencies

| Dependency | Version | Impact | Notes |
|------------|---------|--------|-------|
| react | 18+ | Compatible | Using hooks |
| leaflet | 1.9.x | Compatible | Tested with clustering |
| react-window | - | NEW | For virtualization |
| typescript | 5.x | Compatible | Strict mode may need updates |

### No Changes Required To

- Backend worker queue system
- Document ingestion pipeline
- Storage backend interfaces
- Parser registry
- Plugin architecture
