# Architectural Requirements — Operation Playback

## Overview

This document contains architectural requirements that must be satisfied regardless of implementation decisions. These are non-negotiable constraints that drive implementation choices.

---

## Backward Compatibility Requirements

### AR1: URL Compatibility

**Requirement:** All existing URLs and query parameters must continue to function.

**Rationale:** Users may have bookmarks or shared links to specific views.

**Current Routes That Must Work:**
```typescript
/trace                              // Main trace view
/trace?view=map                    // Map view
/trace?view=timeline              // Timeline view (placeholder)
/trace?view=grid                  // Grid view (placeholder)
```

**Filter Parameters That Must Work:**
```typescript
/trace?cameras=HONOR,Xiaomi      // Device filter
/trace?years=2025,2026           // Years filter (deprecated but functional)
/trace?startDate=2025-01-01      // Date range start
/trace?endDate=2025-12-31        // Date range end
/trace?collections=...           // Collection filter
```

**Migration Path:**
- `years` parameter should be converted to date range equivalent
- URL redirect for deprecated parameters
- Deep links to specific photos must continue to work

---

### AR2: API Contract Compatibility

**Requirement:** Existing API endpoints must maintain backward compatibility.

**Current Endpoints:**
```python
GET /api/trace                    # Returns markers, events, stats
GET /api/trace/filters            # Returns filter groups
GET /api/trace/thumbnail/{path}   # Serves thumbnail
```

**Compatibility Rules:**
- Response structure must not change for existing fields
- New optional fields may be added
- Existing fields cannot be removed or renamed
- Pagination additions must be backward compatible

**Breaking Changes Policy:**
- Breaking changes require API version increment (v1 → v2)
- Old API versions supported for minimum 6 months

---

### AR3: Component Props Compatibility

**Requirement:** Existing component interfaces must not break.

**TraceView.tsx Props:** (None - no props, self-contained)

**FilmStrip.tsx Props:**
```typescript
interface FilmStripProps {
  filters: FilterState           // Cannot change
  onThumbnailClick?: (item: TraceEventItem) => void  // Cannot change
  selectedThumbnailId?: number   // Cannot change
  scrollToThumbnailId?: number  // Cannot change (used for sync)
}
```

**MapCanvas.tsx Props:**
```typescript
interface MapCanvasProps {
  filters: FilterState           // Cannot change
  onMarkerClick?: (marker: TraceMapMarker) => void  // Cannot change
  selectedMarkerId?: number     // Cannot change
  centerOnMarkerId?: number     // Cannot change (used for sync)
}
```

**New Props:** May be added as optional

---

### AR4: State Shape Compatibility

**Requirement:** FilterState interface cannot break existing code.

**Current FilterState:**
```typescript
interface FilterState {
  cameras: string[]
  collections: string[]
  years: string[]
  sources: string[]
  startDate: string | null
  endDate: string | null
  includeUnknownDevice: boolean
  timePreset?: TimePreset | null
}
```

**Migration Rule:**
- `years` field: Deprecate but keep in interface during transition
- Mark as optional during deprecation period
- Remove only after URL redirect is verified

---

## Performance Requirements

### AR5: Initial Load Time

**Requirement:** First meaningful paint within 2 seconds for 100k collection.

**Breakdown:**
- First paint: < 1 second (loading skeleton visible)
- Interactive: < 3 seconds (filters and first items visible)
- Full data: Background progressive load

**Measurement:** Chrome DevTools Performance panel, Lighthouse

---

### AR6: Playback Frame Rate

**Requirement:** Minimum 30fps during playback for collections up to 100k.

**Measurement:** Chrome DevTools Performance panel, requestAnimationFrame timing

**Thresholds:**
- 30fps minimum during playback
- Map animations at 60fps preferred
- UI responsiveness < 100ms

---

### AR7: Memory Usage

**Requirement:** Browser memory usage < 500MB for 100k photo metadata.

**Measurement:** Chrome DevTools Memory panel, performance.memory API

**Strategies Required:**
- Virtual scrolling for DOM elements
- Thumbnail lazy loading
- Event cleanup on unmount
- No memory leaks in animation loops

---

### AR8: Marker Scaling

**Requirement:** Map must remain interactive with up to 500 visible markers.

**Measurement:** Performance profiling with 100/500/1000/5000 markers

**Clustering Requirement:**
- Cluster markers when density exceeds threshold
- Clusters must be interactive (expandable)
- Clustering must not degrade with zoom level

---

### AR9: Virtual Scrolling

**Requirement:** Filmstrip must use virtualization for 100k+ items.

**Measurement:** DOM node count, scroll performance

**Requirements:**
- DOM nodes: < 1000 regardless of collection size
- Scroll performance: 60fps
- No layout shift during scroll

---

## Synchronization Requirements

### AR10: Sync Latency

**Requirement:** Synchronization between views must be < 100ms perceived latency.

**Measurement:** User-perceived delay between interactions

**Synchronization Events:**
| Trigger | Expected Response |
|---------|-----------------|
| Filmstrip click | Map centers in < 100ms |
| Map click | Filmstrip scrolls in < 100ms |
| Timeline drag | All views update in < 100ms |
| Playback advance | All views update in < 100ms |

---

### AR11: Feedback Loop Prevention

**Requirement:** No infinite loops or feedback cascades during synchronization.

**Implementation:**
```typescript
interface SyncState {
  isSyncing: boolean  // Prevent feedback when true
}

// When syncing:
// 1. Set isSyncing = true
// 2. Update all components
// 3. Set isSyncing = false
```

---

### AR12: Playhead Position Tracking

**Requirement:** Current playhead position must be trackable and shareable.

**State Requirements:**
- `playheadPosition: string | null` (ISO timestamp)
- `currentFrameIndex: number`
- Both must be serializable to URL

---

## Accessibility Requirements

### AR13: Keyboard Navigation

**Requirement:** All playback controls must be keyboard accessible.

**Minimum Required Shortcuts:**
| Key | Action |
|-----|--------|
| Space | Play/Pause toggle |
| S | Stop |
| ← / → | Step backward/forward |
| Home / End | Jump to start/end |

**Measurement:** Manual testing with keyboard-only navigation

---

### AR14: Screen Reader Support

**Requirement:** Screen readers must announce state changes.

**Required Announcements:**
- Playback state changes (playing, paused, stopped)
- Current photo information on change
- Timeline position changes

**Measurement:** VoiceOver (macOS), NVDA (Windows)

---

### AR15: Color Contrast

**Requirement:** WCAG 2.1 AA compliance for all UI elements.

**Measurement:** Lighthouse accessibility audit, axe DevTools

**Thresholds:**
- Text: 4.5:1 contrast ratio
- Large text: 3:1 contrast ratio
- UI components: 3:1 contrast ratio

---

## Security Requirements

### AR16: Thumbnail Access Control

**Requirement:** Thumbnails must only be served to authenticated users.

**Implementation:**
- Verify authentication before serving
- Validate path to prevent directory traversal
- Rate limiting on thumbnail endpoint

---

### AR17: Input Sanitization

**Requirement:** All user inputs (filters, timestamps) must be sanitized.

**Implementation:**
- Validate date formats
- Sanitize string parameters
- Limit array lengths for multi-select filters

---

## Browser Support Requirements

### AR18: Modern Browser Support

**Requirement:** Must support latest 2 versions of major browsers.

**Supported Browsers:**
| Browser | Minimum Version |
|---------|----------------|
| Chrome | Latest - 1 |
| Firefox | Latest - 1 |
| Safari | Latest - 1 |
| Edge | Latest - 1 |

**Measurement:** BrowserStack or similar testing

---

### AR19: Mobile Browser Support

**Requirement:** Basic functionality on mobile browsers (iOS Safari, Chrome Mobile).

**Measurement:** Physical device testing or BrowserStack

**Graceful Degradation:**
- Full functionality on desktop
- Core features work on mobile
- Playback controls touch-friendly

---

## Data Integrity Requirements

### AR20: Timestamp Handling

**Requirement:** All photos must have a usable timestamp.

**Fallback Chain:**
1. EXIF DateTimeOriginal
2. EXIF DateTime
3. File modification time
4. File creation time
5. Current server time (last resort)

---

### AR21: Missing GPS Handling

**Requirement:** Photos without GPS data must not break map visualization.

**Implementation:**
- Filter non-GPS items from map markers
- Filmstrip/timeline show all items
- Visual indicator for items without GPS

---

## Summary Table

| ID | Requirement | Type | Priority |
|----|-------------|------|----------|
| AR1 | URL Compatibility | Backward Compat | Critical |
| AR2 | API Contract | Backward Compat | Critical |
| AR3 | Component Props | Backward Compat | Critical |
| AR4 | State Shape | Backward Compat | High |
| AR5 | Initial Load < 2s | Performance | High |
| AR6 | 30fps Playback | Performance | High |
| AR7 | < 500MB Memory | Performance | High |
| AR8 | 500 Marker Limit | Performance | High |
| AR9 | Virtual Scrolling | Performance | High |
| AR10 | < 100ms Sync | Synchronization | High |
| AR11 | No Feedback Loops | Synchronization | Critical |
| AR12 | Playhead Tracking | Synchronization | Medium |
| AR13 | Keyboard Nav | Accessibility | High |
| AR14 | Screen Reader | Accessibility | Medium |
| AR15 | Color Contrast | Accessibility | High |
| AR16 | Thumbnail Auth | Security | High |
| AR17 | Input Sanitization | Security | High |
| AR18 | Modern Browsers | Browser Support | High |
| AR19 | Mobile Support | Browser Support | Medium |
| AR20 | Timestamp Fallback | Data Integrity | High |
| AR21 | Missing GPS Handling | Data Integrity | High |

**Total Requirements:** 21
**Critical:** 5
**High:** 13
**Medium:** 3
