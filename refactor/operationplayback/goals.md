# Goals — Operation Playback

## Primary Goals

### 1. Timeline X-axis as Primary Navigation

**Goal:** Replace the discrete years filter with a continuous, interactive timeline that serves as the primary navigation mechanism.

**Acceptance Criteria:**
- Timeline spans full workspace width
- User can drag playhead to any position
- Timeline shows date labels at appropriate intervals (day/week/month based on zoom)
- Timeline responds to filter changes (shows only filtered range)
- Timeline is keyboard accessible

**Relationship to Current Code:**
- `FilterPalette.tsx` — Years filter group will be removed or replaced
- New `TimelineAxis` component will be created
- `TraceView.tsx` — Layout reorganization to accommodate timeline

### 2. Playback Controls Integration

**Goal:** Add video-like playback controls that allow users to play through their photo collection.

**Acceptance Criteria:**
- Play/Pause toggle (Space key)
- Stop button returns to start
- Speed control: 0.5x, 1x, 2x, 4x, 8x, 16x
- Step forward/backward one frame (arrow keys)
- Visual progress indicator showing current position

**Relationship to Current Code:**
- New `PlaybackControls` component
- Integration with `TraceView.tsx` state management

### 3. Forward Playback

**Goal:** Chronological playback through filtered items, automatically advancing through frames.

**Acceptance Criteria:**
- Playback advances through items in timestamp order (oldest to newest)
- Configurable speed (frames per second equivalent)
- Playback respects current filters
- Playback pauses at end of collection
- Playback can be interrupted (pause, click, filter change)

### 4. Reverse Playback

**Goal:** Traverse history backwards in time, allowing users to "unwind" through their collection.

**Acceptance Criteria:**
- Reverse button toggles playback direction
- Visual indicator shows current direction (forward/reverse)
- Reverse playback at same speed as forward
- Seamless transition between forward and reverse
- Boundary handling (stop at earliest/latest photo)

### 5. Thumbnail Hover Preview

**Goal:** On hover over filmstrip frames, show an enlarged preview of the photo.

**Acceptance Criteria:**
- Hover over thumbnail shows popup with larger image
- Preview includes timestamp and camera metadata
- Preview appears after 200ms hover delay
- Preview disappears on mouse leave
- Preview positioned to not obscure other elements

**Relationship to Current Code:**
- Enhancement to `FilmStrip.tsx`
- New hover preview component

### 6. Marker Hover Preview

**Goal:** On hover over map markers, show thumbnail preview with key metadata.

**Acceptance Criteria:**
- Hover over map marker shows tooltip with thumbnail
- Tooltip shows filename, timestamp, camera
- Tooltip positioned above marker
- Tooltip auto-dismisses on mouse leave
- Clustered markers show count and expand on hover

**Relationship to Current Code:**
- Enhancement to `MapCanvas.tsx`
- Integration with Leaflet marker tooltips

### 7. Synchronized Views

**Goal:** Map, filmstrip, and timeline maintain synchronization during all interactions.

**Acceptance Criteria:**
- Clicking filmstrip frame centers map on that photo's location
- Clicking map marker scrolls filmstrip to that frame
- Dragging timeline playhead updates both map and filmstrip
- Playback mode: all views advance together
- Synchronization has <100ms perceived latency

**Relationship to Current Code:**
- `TraceView.tsx` — Centralized synchronization state
- `FilmStrip.tsx` — `scrollToThumbnailId` prop already exists
- `MapCanvas.tsx` — `centerOnMarkerId` prop already exists

### 8. Removal of Years Filter

**Goal:** Replace the discrete years filter with continuous timeline navigation.

**Acceptance Criteria:**
- Years filter group removed from FilterPalette
- TimeRange filter updated to use continuous dates
- Timeline X-axis replaces year selection
- Existing year-filtered URLs gracefully redirect
- Performance: timeline works with collections spanning decades

**Relationship to Current Code:**
- `FilterPalette.tsx` — Remove years filter group
- `FilterState` interface — Remove `years` field
- API endpoints — `years` parameter deprecated

### 9. Removal of Event Stream

**Goal:** Replace the EventStream component with the integrated Timeline X-axis.

**Acceptance Criteria:**
- EventStream component removed
- Timeline X-axis shows all filtered items
- Clicking timeline item selects that photo
- Timeline supports scrolling through large collections
- Timeline maintains current scroll position on filter change

**Relationship to Current Code:**
- `EventStream.tsx` — To be removed
- `TraceView.tsx` — Remove EventStream import and usage
- `FilmStrip.tsx` — May expand to cover former EventStream space

### 10. Expanded Filmstrip Mode

**Goal:** Make the filmstrip larger and more prominent, becoming the primary content view.

**Acceptance Criteria:**
- Filmstrip height increased from ~120px to ~240px (configurable)
- Filmstrip shows larger thumbnails (150px vs current ~80px)
- Filmstrip scroll indicators for long collections
- Filmstrip maintains selection center-screen during playback
- Optional: Fullscreen filmstrip mode

**Relationship to Current Code:**
- `FilmStrip.tsx` — Redesign with larger frames
- `FilmStrip.css` — Updated styling
- `TraceView.tsx` — Adjusted layout proportions

### 11. Scalability for 100k+ Images

**Goal:** Support large collections without performance degradation.

**Acceptance Criteria:**
- Virtual scrolling in filmstrip (only render visible frames)
- Marker clustering on map (max 500 visible markers)
- Pagination in API (max 200 items per request)
- Lazy loading of thumbnails
- Timeline summarization (clusters at far zoom, details at close zoom)
- Initial load <2 seconds for 100k collection
- Playback smooth at 30fps for 100k collection

**Relationship to Current Code:**
- `FilmStrip.tsx` — Add virtualization (react-window or similar)
- `MapCanvas.tsx` — Already uses clustering, may need adjustment
- API — Add cursor-based pagination

---

## Non-Goals (Explicitly Out of Scope)

1. **Video export** — Saving playback as video file
2. **Audio soundtrack** — Adding background music
3. **AI captions** — Auto-generating descriptions
4. **Collaboration** — Sharing playback sessions
5. **Annotations** — Drawing on photos during playback
6. **Comparison mode** — Side-by-side photo comparison

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Time in Trace per session | ~2 min | ~6 min | Analytics |
| Photos viewed per session | ~10 | ~30 | Analytics |
| Filter usage rate | 40% | 60% | Analytics |
| Playback initiation rate | N/A | 30% | Analytics |
| Page load time (100k) | ~10s | ~2s | Performance |
| Playback frame rate | N/A | 30fps | Performance |

---

## Dependencies Between Goals

```
Timeline X-axis (Goal 1)
    │
    ├── Required by: Playback Controls (Goal 2)
    ├── Required by: Synchronization (Goal 7)
    └── Required by: Removal of Years Filter (Goal 8)
         │
         └── Required by: Removal of Event Stream (Goal 9)

Playback Controls (Goal 2)
    │
    ├── Required by: Forward Playback (Goal 3)
    └── Required by: Reverse Playback (Goal 4)

Forward Playback (Goal 3)
    │
    └── Required by: Reverse Playback (Goal 4)

Scalability (Goal 11)
    │
    ├── Required by: All other goals
    └── Priority: Implement first or alongside
```

---

## Priority Order

1. **P1 - Scalability (Goal 11)** — Must be foundation
2. **P2 - Timeline X-axis (Goal 1)** — Core navigation
3. **P3 - Synchronization (Goal 7)** — Core UX
4. **P4 - Playback Controls (Goal 2)** — Core interaction
5. **P5 - Forward Playback (Goal 3)** — Core feature
6. **P6 - Hover Previews (Goals 5, 6)** — Polish
7. **P7 - Reverse Playback (Goal 4)** — Secondary feature
8. **P8 - Expanded Filmstrip (Goal 10)** — Visual improvement
9. **P9 - Removal of Years/EventStream (Goals 8, 9)** — Cleanup
