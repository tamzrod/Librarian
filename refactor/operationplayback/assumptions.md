# Assumptions — Operation Playback

## Technical Assumptions

### A1: Frontend Framework Compatibility

**Assumption:** The current React/TypeScript frontend stack is suitable for implementing Operation Playback without major framework changes.

**Supporting Evidence:**
- Current codebase uses React 18+
- TypeScript for type safety
- Existing state management patterns in `TraceView.tsx`
- CSS-based styling (no heavy framework dependencies)

**Mitigation:** If React Server Components or other framework changes are planned, they may conflict with Operation Playback implementation.

### A2: API Support for Pagination

**Assumption:** The backend API can support cursor-based pagination for large collections.

**Current State:**
- `api.getTraceData()` already accepts `limit` parameter
- Response includes `markers` and `events` arrays
- No cursor/token pagination currently implemented

**Requirements:**
- Cursor-based pagination to avoid offset performance issues at scale
- API endpoint supporting `after` and `before` cursors
- API response including `next_cursor` and `has_more` fields

**Mitigation:** May require API changes as part of Operation Playback.

### A3: Leaflet Performance

**Assumption:** Leaflet can handle 500+ markers with clustering without significant performance issues.

**Supporting Evidence:**
- Leaflet is battle-tested for marker-heavy maps
- Current implementation already uses basic clustering
- `markercluster` plugin available for advanced clustering

**Mitigation:** If Leaflet proves insufficient, consider MapLibre GL JS or deck.gl for WebGL-based rendering.

### A4: Browser Performance

**Assumption:** Target browsers (Chrome, Firefox, Safari, Edge) have sufficient performance for:
- 60fps playback animation
- Virtual scrolling with 100k+ items
- Real-time map rendering

**Mitigation:** May need to detect browser capabilities and provide fallbacks.

### A5: State Management

**Assumption:** React Context + useState in `TraceView.tsx` is sufficient for Operation Playback state.

**Current Pattern:**
- `TraceView.tsx` manages: `filters`, `viewMode`, `selectedDocumentId`, `scrollToThumbnailId`, `centerOnMarkerId`

**New State Requirements:**
- `playbackState`: 'stopped' | 'playing' | 'paused'
- `playbackDirection`: 'forward' | 'reverse'
- `playbackSpeed`: number (multiplier)
- `playheadPosition`: timestamp
- `currentFrameIndex`: number

**Mitigation:** May need Zustand or Redux if state becomes complex.

---

## User Experience Assumptions

### A6: Keyboard Navigation

**Assumption:** Users expect full keyboard accessibility for playback controls.

**Expected Keyboard Shortcuts:**
| Key | Action |
|-----|--------|
| Space | Play/Pause |
| S | Stop |
| R | Toggle Reverse |
| ← / → | Step backward/forward |
| Shift+← / Shift+→ | Skip 10 frames |
| Home | Go to start |
| End | Go to end |
| + / - | Speed up/down |

### A7: Progressive Disclosure

**Assumption:** Users prefer a simple interface by default, with advanced features accessible via expansion.

**Design Implication:**
- Playback controls visible by default
- Speed controls visible but secondary
- Frame-by-frame controls visible but tertiary
- Reverse playback accessible but not prominent

### A8: Mobile Responsiveness

**Assumption:** Operation Playback is primarily a desktop experience, with basic mobile support.

**Mobile Considerations:**
- Touch-friendly playback controls (larger tap targets)
- Simplified filmstrip (fewer visible frames)
- Map might be secondary on mobile (filmstrip primary)
- Timeline might become secondary on mobile

**Mitigation:** Responsive breakpoints with mobile-first filmstrip.

### A9: Collection Size Distribution

**Assumption:** Most users have collections under 10k photos, but 10% have 100k+.

**Design Implication:**
- Performance must scale to 100k
- UI must remain usable at 100 items
- Clustering/summarization essential for large collections

---

## Architectural Assumptions

### A10: Backward Compatibility

**Assumption:** Existing URLs and routes must continue to work.

**Current Routes:**
- `/trace` — Main trace view
- `/trace?view=map` — Map view
- `/trace?view=timeline` — Timeline view (placeholder)
- `/trace?view=grid` — Grid view (placeholder)

**Requirements:**
- Old filter parameters (`years`, `cameras`, etc.) must continue to work
- Filter state should be serializable to URL
- Deep links to specific photos should continue to work

### A11: Filter State Persistence

**Assumption:** Users expect filters to persist across sessions.

**Current Behavior:**
- Filters are local state (not persisted)
- No save/load filter presets

**Operation Playback Addition:**
- Timeline position should be restorable
- Filter presets should be savable

### A12: Multi-Tab Synchronization

**Assumption:** Users may have multiple tabs open with the same collection.

**Requirements:**
- Each tab has independent playback state
- No cross-tab synchronization required initially

---

## Data Assumptions

### A13: Timestamp Reliability

**Assumption:** EXIF timestamps are generally reliable, with outliers that need handling.

**Edge Cases to Handle:**
- Missing EXIF data → Use file creation time as fallback
- Future dates → Clamp to reasonable range
- Dates before 1990 → Accept (digitization of old photos)
- Timezone handling → Store and display in local time

### A14: GPS Data Completeness

**Assumption:** ~40% of photos have GPS data (based on current stats).

**Implications:**
- Map visualization is secondary to filmstrip
- Photos without GPS still appear in filmstrip/timeline
- Clustered markers only for photos with GPS

### A15: Thumbnail Availability

**Assumption:** Thumbnails are generated for all images during ingestion.

**Current State:**
- `thumbnail_generator` worker exists
- Thumbnails stored on filesystem
- Thumbnail URLs served via API

**Requirements:**
- Thumbnails must be available for all images
- Lazy loading must not cause flash of content

---

## Performance Assumptions

### A16: Initial Load Time

**Assumption:** Users will tolerate a 2-3 second initial load for large collections.

**Target:**
- First paint: <1 second
- Interactive: <3 seconds
- Full data load: Background (progressive)

**Mitigation:** Show loading skeleton immediately.

### A17: Playback Frame Rate

**Assumption:** 30fps playback is achievable for 100k collections.

**Target:**
- Playback: 30fps minimum
- Map animation: 60fps
- UI responsiveness: 100ms maximum

### A18: Memory Usage

**Assumption:** Browser can handle 100k photo metadata in memory.

**Target:**
- Memory usage: <500MB for 100k items
- Virtual scrolling keeps DOM nodes under 1000

---

## Conflict Assumptions

### A19: P16-Trace-Concept Alignment

**Assumption:** Operation Playback is aligned with P16-Trace-Concept vision.

**From P16-Trace-Concept:**
- Phase 2: Advanced Playback
- Playback controls: Play/Pause/Stop, Speed, Frame-by-frame
- Timeline scrubbing

**Conflict Check:** See [conflict-analysis-template.md](./conflict-analysis-template.md)

### A20: No Conflict with Operation EXIF

**Assumption:** Operation Playback does not conflict with Operation EXIF metadata work.

**Operation EXIF Focus:**
- Metadata ownership
- Thumbnail persistence
- Location aggregation

**Potential Conflict:** If Operation EXIF changes thumbnail API, Operation Playback may need updates.

**Mitigation:** Coordinate with Operation EXIF team.

---

## Open Assumptions (Requiring Validation)

### OA1: Playback Speed Defaults

**Question:** What should the default playback speed be?

**Options:**
- 1 photo/second (cinematic)
- 2 photos/second (standard)
- 4 photos/second (fast)

**Current Thinking:** 1 photo/second (1x speed = 1 photo per second)

### OA2: Frame Step Size

**Question:** What does "step" mean?

**Options:**
- Step = 1 photo
- Step = 1 second of real time (may skip multiple photos)
- Step = 1 cluster of similar photos

**Current Thinking:** Step = 1 photo (most predictable)

### OA3: Timeline Granularity

**Question:** How detailed should the timeline be?

**Options:**
- Show all photos (too cluttered for large collections)
- Show aggregated buckets (day/week/month)
- Show significant moments only

**Current Thinking:** Zoom-dependent (see scalability goals)

---

## Assumption Review Checklist

Before implementation, validate:

- [ ] API pagination support confirmed
- [ ] Leaflet performance acceptable for 500+ markers
- [ ] Browser targets confirmed
- [ ] Keyboard shortcuts don't conflict with OS/browser
- [ ] Mobile use cases defined
- [ ] Collection size distribution validated
- [ ] Backward compatibility requirements confirmed
- [ ] Timestamp edge cases documented
- [ ] Memory usage acceptable
- [ ] Playback speed defaults validated with users
