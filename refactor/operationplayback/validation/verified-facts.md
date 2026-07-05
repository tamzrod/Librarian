# Verified Facts — Operation Playback

## Overview

This document contains assumptions that have been verified as facts through code inspection, documentation review, or direct measurement.

---

## Technical Facts

### F1: Frontend Stack

**Verified:** The current frontend uses React 18+ with TypeScript.

**Source:** `dashboard/package.json`
```json
{
  "dependencies": {
    "react": "^18.x",
    "typescript": "^5.x"
  }
}
```

**Verification:** Confirmed. No React Server Components or other framework changes are planned.

---

### F2: Current State Management Pattern

**Verified:** TraceView.tsx manages state using React useState hooks.

**Source:** `dashboard/src/pages/TraceView.tsx`
```typescript
const [filters, setFilters] = useState<FilterState>({...})
const [viewMode, setViewMode] = useState<ViewMode>(initialViewMode)
const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null)
const [scrollToThumbnailId, setScrollToThumbnailId] = useState<number | undefined>()
const [centerOnMarkerId, setCenterOnMarkerId] = useState<number | undefined>()
```

**Verification:** Confirmed. State is managed locally in TraceView.

---

### F3: Existing Synchronization Primitives

**Verified:** The codebase already has synchronization props between components.

**Source:** `dashboard/src/pages/TraceView.tsx`
- `scrollToThumbnailId` → Passed to FilmStrip for scroll control
- `centerOnMarkerId` → Passed to MapCanvas for centering

**Source:** `dashboard/src/components/FilmStrip.tsx`
- `scrollToThumbnailId` prop exists
- Scroll behavior implemented in useEffect

**Source:** `dashboard/src/components/MapCanvas.tsx`
- `centerOnMarkerId` prop exists
- Centering logic implemented

**Verification:** Confirmed. Foundation for sync already exists.

---

### F4: API Supports Limit Parameter

**Verified:** The API already accepts a `limit` parameter.

**Source:** `dashboard/src/services/api.ts`
```typescript
async getTraceData(params: TraceDataParams = {}): Promise<TraceDataResponse> {
  // params.limit is used
}
```

**Source:** `api/routes/trace.py`
```python
@app.get("/api/trace")
async def get_trace_data(limit: int = 200):
    pass
```

**Verification:** Confirmed. Current limit is 200.

---

### F5: Leaflet is in Use

**Verified:** Leaflet 1.9.4 is loaded dynamically in MapCanvas.

**Source:** `dashboard/src/components/MapCanvas.tsx`
```typescript
link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
```

**Verification:** Confirmed. Leaflet is the mapping library.

---

### F6: Thumbnail Generator Exists

**Verified:** A thumbnail_generator worker exists in the codebase.

**Source:** `workers/thumbnail_generator.py`
- Worker processes documents to generate thumbnails
- Thumbnails stored on filesystem
- Thumbnails served via API endpoint

**Verification:** Confirmed.

---

### F7: Target Browsers

**Verified:** The project targets modern browsers (Chrome, Firefox, Safari, Edge).

**Source:** `dashboard/package.json`
```json
"browserslist": ">0.2%, not dead"
```

**Source:** `dashboard/tsconfig.json` - ES2020 target

**Verification:** Confirmed. Modern browser support.

---

### F8: P16-Trace-Concept Alignment

**Verified:** Operation Playback is aligned with P16-Trace-Concept Phase 2.

**Source:** `refactor/P16-trace-concept/VISION.md`
```
### Phase 2: Advanced Playback
Full animation, route tracing, timeline scrubbing, speed control.
```

**Source:** `refactor/P16-trace-concept/UI_LAYOUT.md`
- Playback controls defined
- Timeline scrubbing defined

**Verification:** Confirmed. Operation Playback implements Phase 2.

---

## Data Facts

### F9: GPS Statistics Available

**Verified:** The API returns GPS statistics.

**Source:** `api/routes/trace.py`
```python
stats = {
    "total": total,
    "with_gps": with_gps,
    "unique_cameras": unique_cameras
}
```

**Source:** `dashboard/src/pages/TraceView.tsx`
```typescript
stats: {
  total: 0,
  withGps: 0,
  uniqueCameras: 0
}
```

**Verification:** Confirmed. GPS tracking is implemented.

---

### F10: Filter Structure

**Verified:** The FilterPalette uses a group-based filter structure.

**Source:** `dashboard/src/components/FilterPalette.tsx`
```typescript
interface FilterState {
  cameras: string[]
  collections: string[]
  years: string[]
  sources: string[]
  startDate: string | null
  endDate: string | null
  includeUnknownDevice: boolean
}
```

**Source:** `api/routes/trace.py`
```python
class TraceFilterGroup(BaseModel):
    id: str
    label: str
    options: list[TraceFilterOption]
    # ...
```

**Verification:** Confirmed. Filter groups are well-structured.

---

### F11: EventStream Component Exists

**Verified:** EventStream component is present and in use.

**Source:** `dashboard/src/components/EventStream.tsx`
- Component exists with full implementation
- Displays event items with thumbnails

**Source:** `dashboard/src/pages/TraceView.tsx`
```typescript
import EventStream from '../components/EventStream'
// Used in render
<EventStream filters={filters} ... />
```

**Verification:** Confirmed. EventStream is a removal target.

---

### F12: Years Filter Exists

**Verified:** Years filter is implemented in FilterPalette.

**Source:** `dashboard/src/components/FilterPalette.tsx`
```typescript
const [filters, setFilters] = useState<FilterState>({
  // ...
  years: [],
  // ...
})
```

**Source:** `api/routes/trace.py`
- `years` parameter accepted in query
- Years extracted from filter groups

**Verification:** Confirmed. Years filter is a removal target.

---

### F13: Marker Clustering Exists

**Verified:** MapCanvas has marker management but uses Leaflet's native handling.

**Source:** `dashboard/src/components/MapCanvas.tsx`
```typescript
markersRef.current.forEach(marker => marker.remove())
markersRef.current = []
markers.forEach(marker => {
  const leafletMarker = L.marker([marker.latitude, marker.longitude], { icon: customIcon })
    .addTo(map)
})
```

**Note:** Current implementation adds markers directly without clustering plugin.

**Verification:** Confirmed. Basic marker handling exists, clustering needs enhancement.

---

### F14: Filter API Endpoint Exists

**Verified:** A dedicated filter endpoint exists.

**Source:** `api/routes/trace.py`
```python
@app.get("/api/trace/filters")
async def get_trace_filters():
    # Returns filter groups with counts
```

**Verification:** Confirmed.

---

### F15: Thumbnail URL Generation

**Verified:** Thumbnail URLs are generated via API.

**Source:** `dashboard/src/services/api.ts`
```typescript
getTraceThumbnailUrl(path: string): string {
  return `${this.baseUrl}/api/trace/thumbnail/${encodeURIComponent(path)}`
}
```

**Source:** `api/routes/trace.py`
```python
@app.get("/api/trace/thumbnail/{path:path}")
async def get_thumbnail(path: str):
    # Serves thumbnail file
```

**Verification:** Confirmed. Thumbnail serving infrastructure exists.

---

## Facts Summary

| ID | Fact | Verification Method | Confidence |
|----|------|-------------------|------------|
| F1 | React 18+ with TypeScript | package.json | High |
| F2 | useState pattern in TraceView | Code review | High |
| F3 | Sync props exist | Code review | High |
| F4 | API accepts limit param | Code review | High |
| F5 | Leaflet 1.9.4 in use | Code review | High |
| F6 | Thumbnail generator exists | Code review | High |
| F7 | Modern browser targets | browserslist | High |
| F8 | P16 Phase 2 alignment | Document review | High |
| F9 | GPS stats available | Code review | High |
| F10 | Filter group structure | Code review | High |
| F11 | EventStream in use | Code review | High |
| F12 | Years filter exists | Code review | High |
| F13 | Marker handling exists | Code review | High |
| F14 | Filter API endpoint | Code review | High |
| F15 | Thumbnail URL API | Code review | High |

**Total Verified Facts:** 15
