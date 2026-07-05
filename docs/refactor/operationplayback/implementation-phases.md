# Implementation Phases — Operation Playback

## Overview

This document outlines the phased implementation approach for Operation Playback, breaking down the work into manageable chunks with clear dependencies and acceptance criteria.

---

## Phase Summary

| Phase | Name | Duration | Risk | Priority |
|-------|------|----------|------|----------|
| 0 | Foundation | 1 week | Low | Required |
| 1 | Scalability | 2 weeks | Medium | P1 |
| 2 | Timeline X-axis | 1 week | Low | P2 |
| 3 | Synchronization | 1 week | Medium | P3 |
| 4 | Playback Controls | 1 week | Low | P4 |
| 5 | Playback Engine | 2 weeks | High | P5 |
| 6 | Hover Previews | 1 week | Low | P6 |
| 7 | Reverse Playback | 1 week | Low | P7 |
| 8 | Filmstrip Expansion | 1 week | Low | P8 |
| 9 | Cleanup | 1 week | Low | P9 |

**Total Estimated Duration:** 11-12 weeks

---

## Phase 0: Foundation

**Goal:** Set up infrastructure for safe, incremental implementation.

### Tasks

1. **Feature Flag System**
   - Implement `featureFlags.ts` configuration
   - Add localStorage override capability
   - Add URL parameter support
   - Document flag management

2. **Analytics Infrastructure**
   - Add playback-related events to analytics
   - Track: playback_started, playback_paused, playback_completed
   - Track: timeline_interaction, hover_preview_shown
   - Set up dashboards

3. **Testing Infrastructure**
   - Set up Playwright/E2E testing
   - Create playback-specific test utilities
   - Add performance benchmarking setup

4. **Documentation**
   - Update component documentation
   - Add architecture decision records
   - Create runbook for Operation Playback

### Deliverables

- Feature flag system operational
- Analytics events defined and implemented
- E2E test framework in place
- Test coverage baseline

### Exit Criteria

- [ ] `FEATURE_FLAGS` config with all planned flags
- [ ] Feature flags controllable via URL
- [ ] Playback analytics events firing
- [ ] Test infrastructure operational
- [ ] All Phase 0 code reviewed and merged

---

## Phase 1: Scalability

**Goal:** Ensure the application can handle 100k+ images without performance degradation.

**Priority:** P1 (Foundation for all other phases)

### Tasks

1. **Virtual Scrolling for FilmStrip**
   - Research and select virtualization library (`react-window` or `@tanstack/react-virtual`)
   - Implement virtualized filmstrip
   - Verify correct scroll behavior
   - Test with 100k items

2. **Map Marker Clustering Enhancement**
   - Evaluate current clustering implementation
   - Add dynamic cluster sizing based on zoom level
   - Limit visible markers to 500
   - Test map performance with dense marker sets

3. **API Pagination Enhancement**
   - Add cursor-based pagination to `/api/trace`
   - Implement `next_cursor` and `has_more` in response
   - Update frontend to handle pagination
   - Add timeline summary endpoint for bucket data

4. **Thumbnail Optimization**
   - Implement thumbnail lazy loading
   - Add thumbnail preloading during idle
   - Consider thumbnail CDN caching strategy

### Deliverables

- FilmStrip virtualizes 100k items smoothly
- Map handles 100k photos with clustering
- API supports cursor pagination
- Thumbnails load progressively

### Exit Criteria

- [ ] FilmStrip renders 100k items at 60fps scroll
- [ ] Map renders 100k markers without lag
- [ ] API returns first page within 500ms
- [ ] Memory usage < 500MB for 100k items
- [ ] No layout shift during loading

### Code Changes

| File | Change |
|------|--------|
| `FilmStrip.tsx` | Add virtualization wrapper |
| `FilmStrip.css` | Update for virtualization |
| `MapCanvas.tsx` | Enhance clustering |
| `api/routes/trace.py` | Add cursor pagination |
| `api.ts` | Update client for pagination |

---

## Phase 2: Timeline X-axis

**Goal:** Create a continuous timeline component as primary navigation.

**Priority:** P2

### Tasks

1. **TimelineAxis Component**
   - Create `TimelineAxis.tsx` component
   - Implement horizontal time axis
   - Add date labels at appropriate intervals
   - Support zoom levels (year/month/week/day)
   - Add draggable playhead

2. **Timeline Integration**
   - Add TimelineAxis to TraceView layout
   - Position above filmstrip, below playback controls
   - Connect to filter state (startDate/endDate)
   - Handle click-to-seek behavior

3. **Timeline API**
   - Create `/api/trace/timeline` endpoint
   - Return bucket aggregations
   - Support bucket_size parameter
   - Cache bucket data for performance

4. **Filter Integration**
   - Timeline updates FilterState startDate/endDate
   - Drag selection on timeline updates date range
   - Existing date pickers continue to work

### Deliverables

- Functional timeline axis component
- Timeline-driven navigation
- Bucket-based data loading
- Zoom level support

### Exit Criteria

- [ ] Timeline displays correctly at all zoom levels
- [ ] Timeline shows correct date range based on filters
- [ ] Clicking timeline updates selection
- [ ] Dragging playhead updates all views
- [ ] Timeline loads efficiently for large date ranges

### Code Changes

| File | Change |
|------|--------|
| `TimelineAxis.tsx` | NEW component |
| `TimelineAxis.css` | NEW styles |
| `TraceView.tsx` | Add timeline layout, state |
| `FilterPalette.tsx` | Timeline integration |
| `api/routes/trace.py` | Add timeline endpoint |

---

## Phase 3: Synchronization

**Goal:** Ensure map, filmstrip, and timeline stay synchronized.

**Priority:** P3

### Tasks

1. **Sync State Management**
   - Add centralized sync state in TraceView
   - Implement `isSyncing` flag to prevent feedback loops
   - Create sync update protocol

2. **Map ↔ FilmStrip Sync**
   - Click filmstrip → Map centers on photo
   - Click map marker → Filmstrip scrolls to photo
   - Playback → Both update together

3. **Timeline ↔ Views Sync**
   - Timeline playhead → Map + Filmstrip update
   - Click any view → Timeline playhead updates
   - Filter change → Timeline range updates

4. **Sync Optimization**
   - Batch updates to prevent re-render cascades
   - Use `requestAnimationFrame` for smooth updates
   - Throttle rapid changes

### Deliverables

- All views synchronized
- No feedback loops
- Smooth transitions
- Keyboard-accessible sync

### Exit Criteria

- [ ] Filmstrip click updates map center
- [ ] Map click scrolls filmstrip
- [ ] Timeline drag updates both map and filmstrip
- [ ] No infinite loop warnings
- [ ] Sync feels instantaneous (<100ms)

### Code Changes

| File | Change |
|------|--------|
| `TraceView.tsx` | Add sync state, handlers |
| `FilmStrip.tsx` | Add sync callbacks |
| `MapCanvas.tsx` | Add sync callbacks |
| `TimelineAxis.tsx` | Add sync callbacks |

---

## Phase 4: Playback Controls

**Goal:** Add video-like playback controls to the interface.

**Priority:** P4

### Tasks

1. **PlaybackControls Component**
   - Create `PlaybackControls.tsx` component
   - Implement play/pause/stop buttons
   - Add speed selector dropdown
   - Add progress bar with scrubber
   - Add time display (current / total)

2. **Keyboard Shortcuts**
   - Space: Play/Pause
   - S: Stop
   - Arrow keys: Step frame
   - Home/End: Jump to start/end
   - +/-: Speed adjustment

3. **Visual Feedback**
   - Play button transforms to Pause when playing
   - Progress bar shows current position
   - Time display updates during playback
   - Direction indicator (forward/reverse arrow)

### Deliverables

- Fully functional playback controls
- Keyboard shortcuts working
- Visual feedback for all states
- Accessible controls

### Exit Criteria

- [ ] Play starts playback from current position
- [ ] Pause freezes playback
- [ ] Stop returns to start
- [ ] Speed changes take effect immediately
- [ ] All keyboard shortcuts work
- [ ] Screen reader announces state changes

### Code Changes

| File | Change |
|------|--------|
| `PlaybackControls.tsx` | NEW component |
| `PlaybackControls.css` | NEW styles |
| `TraceView.tsx` | Add playback handlers |
| `App.tsx` or `index.tsx` | Global keyboard listeners |

---

## Phase 5: Playback Engine

**Goal:** Implement the actual playback logic for forward and reverse.

**Priority:** P5

### Tasks

1. **Playback State Machine**
   - Implement state: stopped → playing ↔ paused → stopped
   - Handle direction: forward / reverse
   - Manage speed multiplier
   - Track current index and timestamp

2. **Animation Loop**
   - Implement `requestAnimationFrame` loop
   - Calculate frame timing based on speed
   - Advance to next/previous item at correct intervals
   - Handle boundary conditions (start/end of collection)

3. **Preloading Strategy**
   - Preload thumbnails ahead of playhead
   - Preload map tiles for upcoming locations
   - Cancel preloads when direction changes

4. **Edge Case Handling**
   - Empty collection
   - Single item
   - Items with missing timestamps
   - Items without GPS (no map marker)
   - Rapid filter changes during playback

### Deliverables

- Smooth playback at all speeds
- Forward and reverse working
- Preloading prevents loading stalls
- Graceful edge case handling

### Exit Criteria

- [ ] Playback runs smoothly at 30fps for 100k items
- [ ] Speed changes take effect immediately
- [ ] Direction changes are seamless
- [ ] No loading stalls during playback
- [ ] Boundary stops playback gracefully

### Code Changes

| File | Change |
|------|--------|
| `TraceView.tsx` | Playback state machine, animation loop |
| `FilmStrip.tsx` | Auto-scroll during playback |
| `MapCanvas.tsx` | Map pan following during playback |

---

## Phase 6: Hover Previews

**Goal:** Add thumbnail preview popups on hover.

**Priority:** P6

### Tasks

1. **FilmStrip Hover Preview**
   - Add hover state to filmstrip frames
   - Create preview popup component
   - Show enlarged thumbnail on hover
   - Display metadata (timestamp, camera)
   - Position popup to avoid clipping

2. **Map Marker Hover Preview**
   - Integrate with Leaflet marker tooltips
   - Custom tooltip with thumbnail
   - Show filename and timestamp
   - Handle clustered markers

3. **Performance Optimization**
   - Delay popup appearance (200ms)
   - Cancel on rapid mouse movement
   - Use CSS transforms for animation
   - Clean up on unmount

### Deliverables

- Hover previews on filmstrip
- Hover previews on map markers
- Smooth animations
- Performance optimized

### Exit Criteria

- [ ] Hover shows preview after 200ms delay
- [ ] Preview includes thumbnail and metadata
- [ ] Preview dismisses on mouse leave
- [ ] No jank during hover
- [ ] Clustered markers show preview on cluster hover

### Code Changes

| File | Change |
|------|--------|
| `FilmStrip.tsx` | Add hover state, preview |
| `FilmStrip.css` | Preview styles |
| `MapCanvas.tsx` | Enhance tooltips |
| `PreviewPopup.tsx` | NEW shared component |

---

## Phase 7: Reverse Playback

**Goal:** Implement backward traversal through history.

**Priority:** P7

### Tasks

1. **Reverse Direction**
   - Add reverse button to PlaybackControls
   - Visual indicator of direction
   - Keyboard shortcut (R key)

2. **Reverse Engine**
   - Modify playback loop for reverse
   - Handle index decrementing
   - Handle end-of-collection (start of time)
   - Seamless forward ↔ reverse transitions

3. **UI Indicators**
   - Arrow direction indicator
   - "Playing backwards" state
   - Time display shows correct direction

### Deliverables

- Full reverse playback support
- Seamless forward/reverse switching
- Clear direction indicators

### Exit Criteria

- [ ] Reverse button toggles direction
- [ ] Playback traverses backwards through time
- [ ] Forward/reverse transitions are instant
- [ ] Direction is clearly indicated
- [ ] Boundary at earliest photo handled

### Code Changes

| File | Change |
|------|--------|
| `PlaybackControls.tsx` | Add reverse button |
| `TraceView.tsx` | Reverse direction logic |
| `PlaybackControls.css` | Direction indicator styles |

---

## Phase 8: Filmstrip Expansion

**Goal:** Make filmstrip larger and more prominent.

**Priority:** P8

### Tasks

1. **Layout Redesign**
   - Increase filmstrip height to 240px
   - Increase thumbnail size to 150px
   - Update layout proportions in TraceView
   - Ensure responsive behavior

2. **Visual Enhancement**
   - Better thumbnail frames
   - Enhanced selection highlight
   - Playhead position indicator
   - Progress overlay

3. **Optional Fullscreen Mode**
   - Add fullscreen toggle
   - Filmstrip expands to fill viewport
   - Map moves to corner or hides
   - Keyboard shortcut (F11)

### Deliverables

- Larger, more visible filmstrip
- Better visual design
- Optional fullscreen mode

### Exit Criteria

- [ ] Filmstrip is 2x larger than before
- [ ] Thumbnails are clearly visible
- [ ] Fullscreen mode works
- [ ] Layout remains responsive
- [ ] No content overlap issues

### Code Changes

| File | Change |
|------|--------|
| `FilmStrip.css` | Size and style updates |
| `FilmStrip.tsx` | Fullscreen logic |
| `TraceView.tsx` | Layout adjustments |

---

## Phase 9: Cleanup

**Goal:** Remove deprecated functionality and finalize.

**Priority:** P9

### Tasks

1. **Remove Years Filter**
   - Remove years filter group from FilterPalette
   - Update FilterState interface
   - Add URL redirect for old `years` param
   - Update API to ignore/deprecate `years`

2. **Remove EventStream**
   - Remove EventStream import from TraceView
   - Delete EventStream component files
   - Remove EventStream CSS
   - Update routing

3. **Code Cleanup**
   - Remove unused imports
   - Clean up commented code
   - Update TypeScript types
   - Optimize bundle size

4. **Final Testing**
   - Full regression test
   - Performance audit
   - Accessibility audit
   - Cross-browser testing

5. **Documentation**
   - Update user documentation
   - Update API documentation
   - Create migration guide
   - Archive old artifacts

### Deliverables

- Years filter removed
- EventStream removed
- Clean codebase
- Complete documentation

### Exit Criteria

- [ ] Years filter not present in UI
- [ ] EventStream not present in UI
- [ ] All old URLs redirect correctly
- [ ] Code passes linting
- [ ] Bundle size optimized
- [ ] All documentation updated

### Code Changes

| File | Change |
|------|--------|
| `FilterPalette.tsx` | Remove years filter |
| `FilterState` interface | Remove years |
| `EventStream.tsx` | DELETE |
| `EventStream.css` | DELETE |
| `TraceView.tsx` | Remove imports |
| `api/routes/trace.py` | Deprecate years param |

---

## Implementation Order Notes

### Critical Path

```
Phase 0 (Foundation)
       │
       ├── Phase 1 (Scalability) ─────────┐
       │                                   │
       │                                   ▼
       └── Phase 2 (Timeline) ──── Phase 3 (Synchronization)
                                          │
                                          ▼
                               Phase 4 (Playback Controls)
                                          │
                                          ▼
                               Phase 5 (Playback Engine)
                                          │
                     ┌────────────────────┼────────────────────┐
                     ▼                    ▼                    ▼
             Phase 6 (Hover)      Phase 7 (Reverse)     Phase 8 (Filmstrip)
                     │                    │                    │
                     └────────────────────┼────────────────────┘
                                          │
                                          ▼
                               Phase 9 (Cleanup)
```

### Parallel Work

Some phases can be worked on in parallel by different developers:

| Developer A | Developer B |
|-------------|-------------|
| Phase 1 (Scalability) | Phase 2 (Timeline) |
| Phase 4 (Controls) | Phase 6 (Hover Previews) |
| Phase 7 (Reverse) | Phase 8 (Filmstrip) |

### Feature Flags During Development

| Phase | Default Flag State |
|-------|-------------------|
| Phase 0 | All flags OFF |
| Phase 1 | `scalability_improvements` ON |
| Phase 2 | `timeline_axis` ON |
| Phase 3 | `playback_sync` ON |
| Phase 4 | `playback_controls` ON |
| Phase 5 | `playback_engine` ON |
| Phase 6 | `hover_previews` ON |
| Phase 7 | `reverse_playback` ON |
| Phase 8 | `expanded_filmstrip` ON |
| Phase 9 | `remove_years_filter` ON, `remove_event_stream` ON |

---

## Effort Estimates

| Phase | Estimated Hours | Complexity | Notes |
|-------|----------------|------------|-------|
| Phase 0 | 20-30 | Medium | Infrastructure work |
| Phase 1 | 40-60 | High | Virtualization, API changes |
| Phase 2 | 20-30 | Medium | New component |
| Phase 3 | 20-30 | Medium | State management |
| Phase 4 | 15-20 | Low | UI component |
| Phase 5 | 30-40 | High | Core algorithm |
| Phase 6 | 15-20 | Low | UI enhancement |
| Phase 7 | 10-15 | Low | Simple extension |
| Phase 8 | 15-20 | Low | Styling work |
| Phase 9 | 20-30 | Medium | Cleanup, testing |

**Total: 205-295 hours (5-7 weeks for 1 developer, 2.5-3.5 weeks for 2 developers)**

---

## Milestones

| Milestone | Phases | Target Date | Criteria |
|-----------|--------|-------------|----------|
| MVP - Basic Playback | 0-5 | Week 6 | Can play through photos |
| Feature Complete | 0-8 | Week 10 | All features implemented |
| Production Ready | 0-9 | Week 12 | Tested, documented, launched |
