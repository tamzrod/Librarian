# Operation Playback - Architectural Spike Report

**Date:** 2026-07-05  
**Status:** Proof-of-Existence Complete  
**Objective:** Determine if a minimal Operation Playback feature can exist within the current Trace architecture

---

## Executive Summary

✅ **VERDICT: YES, a minimal playback controller CAN synchronize filmstrip, map, and selected image without architectural conflicts.**

The existing Trace architecture already provides the necessary synchronization primitives. The playback feature can be layered on top without requiring changes to core components.

---

## What Was Implemented

A minimal vertical slice demonstrating synchronized playback:

### Components Created

1. **`/dashboard/src/hooks/usePlaybackController.ts`**
   - State machine: `stopped | playing`
   - Interval-based advancement (1 second per step)
   - Exposes: `play()`, `stop()`, `currentIndex`, `isPlaying`

2. **`/dashboard/src/components/PlaybackControls.tsx`**
   - Play button (▶)
   - Stop button (⏹)
   - Position indicator (current / total)

3. **TraceView.tsx Integration**
   - Added playback state management
   - Synchronization effect that triggers:
     - `scrollToThumbnailId` → FilmStrip scrolls to current frame
     - `centerOnMarkerId` → MapCanvas centers on current GPS location
     - `selectedDocumentId` → Updates selected state

### Scope of Implementation

| Feature | Status |
|---------|--------|
| Play button | ✅ Implemented |
| Stop button | ✅ Implemented |
| Advance every second | ✅ Implemented |
| Update selected thumbnail | ✅ Implemented |
| Center map on GPS | ✅ Implemented |
| Reverse playback | ❌ Not implemented |
| Speed controls | ❌ Not implemented |
| Timeline | ❌ Not implemented |
| Hover previews | ❌ Not implemented |
| Keyboard shortcuts | ❌ Not implemented |
| Mobile support | ❌ Not implemented |
| Persistence | ❌ Not implemented |

---

## Architecture Findings

### 1. Existing Synchronization Mechanisms Are Sufficient

The TraceView already orchestrates three-way synchronization:

```
TraceView State:
├── selectedDocumentId ──────┐
├── scrollToThumbnailId ─────┼──▶ FilmStrip
└── centerOnMarkerId ───────┴──▶ MapCanvas
```

**Key Insight:** The playback controller simply drives these existing triggers at timed intervals.

### 2. Component Coupling Analysis

| Coupling Type | Level | Notes |
|---------------|-------|-------|
| TraceView ↔ FilmStrip | Low | Props interface stable: `selectedThumbnailId`, `scrollToThumbnailId` |
| TraceView ↔ MapCanvas | Low | Props interface stable: `selectedMarkerId`, `centerOnMarkerId` |
| FilmStrip ↔ MapCanvas | None | No direct coupling - mediated through TraceView |
| PlaybackController ↔ Components | Indirect | Drives via TraceView state |

### 3. State Ownership Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                        TraceView (OWNER)                         │
│                                                                  │
│  State Owned:                                                    │
│  ├── filters ──────────────▶ FilterPalette                        │
│  ├── selectedDocumentId ──▶ FilmStrip (selectedThumbnailId)     │
│  ├── scrollToThumbnailId ──▶ FilmStrip (scrollIntoView)         │
│  ├── centerOnMarkerId ─────▶ MapCanvas (setView)                │
│  ├── playbackMode ─────────▶ PlaybackControls                    │
│  └── playbackIndex ────────▶ PlaybackControls                    │
│                                                                  │
│  Children (Leaf Components - No State):                           │
│  ├── MapCanvas (renders markers, handles map interactions)        │
│  ├── FilmStrip (renders thumbnails, handles clicks)              │
│  ├── PlaybackControls (renders buttons, emits events)           │
│  └── EventStream (deprecated - candidate for removal)            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Finding:** PlaybackController is NOT a component - it's a hook. It belongs inside TraceView and does not require its own component tree.

### 4. Data Flow During Playback

```
User presses Play
        │
        ▼
usePlaybackController.play()
        │
        ▼
Interval fires (1s)
        │
        ▼
playbackIndex++
        │
        ├──▶ TraceView re-renders
        │         │
        │         ▼
        │    PlaybackControls shows new position
        │
        ▼
Playback synchronization effect runs:
        │
        ├──▶ setScrollToThumbnailId(documentId)
        │         │
        │         ▼
        │    FilmStrip scrolls to frame
        │
        ├──▶ setCenterOnMarkerId(documentId)
        │         │
        │         ▼
        │    MapCanvas centers on GPS
        │
        └──▶ setSelectedDocumentId(documentId)
                  │
                  ▼
             FilmStrip highlights frame
```

---

## Identified Coupling Points

### A. Required Coupling (Unavoidable)

| Point | Direction | Reason |
|-------|-----------|--------|
| TraceView → PlaybackControls | Props | Must pass handlers and display state |
| TraceView → FilmStrip | Props + State | Must control scroll and selection |
| TraceView → MapCanvas | Props + State | Must control center and selection |

### B. Shared State (Acceptable)

The following state is shared and must remain stable:

```typescript
// TraceView owns these - playback depends on them
interface SharedState {
  scrollToThumbnailId: number | undefined
  centerOnMarkerId: number | undefined
  selectedDocumentId: number | null
}
```

### C. Potential Feedback Loops

⚠️ **Risk Identified:** The existing architecture has a potential feedback loop:

```
User clicks thumbnail
        │
        ▼
handleThumbnailClick()
        │
        ├──▶ setScrollToThumbnailId(id)
        ├──▶ setSelectedDocumentId(id)
        └──▶ setCenterOnMarkerId(id) ← clears immediately after use

TraceView renders
        │
        └──▶ FilmStrip re-renders (already scrolled, minor perf hit)
```

**Current Mitigation:** The triggers are cleared after use via `useEffect` with `setTimeout`. This pattern works but is fragile.

**Production Recommendation:** Use a "trigger version" pattern instead:

```typescript
// Instead of: scrollToThumbnailId = documentId
// Use: scrollToThumbnailId = { id: documentId, version: version++ }

// Component clears trigger by checking version
```

---

## Recommendations for Production Implementation

### 1. Architectural Decision: Centralized Playback State

**Recommendation:** Keep playback state in TraceView, NOT in a separate context.

**Rationale:**
- TraceView is already the orchestration point
- Adding React Context would increase indirection without benefit
- The playback controller is effectively a specialized state machine

### 2. Component Extraction

**Recommendation:** Extract a `<PlaybackBar>` wrapper component.

```
TraceView
  └── PlaybackBar (NEW - wraps PlaybackControls + position display)
        └── PlaybackControls (already exists)
```

This allows the playback bar to be repositioned (e.g., above map, below filmstrip) without modifying TraceView logic.

### 3. Synchronization Protocol

**Recommendation:** Add explicit synchronization mode to prevent feedback loops.

```typescript
interface TraceViewState {
  // ... existing
  playback: {
    mode: 'stopped' | 'playing'
    index: number
    source: 'playback' | 'user'  // NEW: prevents feedback loops
  }
}
```

When `source === 'playback'`, user interactions should not interrupt playback state.

### 4. Speed Control (Future)

**Recommendation:** Add speed multiplier to PlaybackController.

```typescript
interface PlaybackOptions {
  interval: number  // milliseconds
}
```

Default: 1000ms (1 second)
Future: 500ms (2x), 200ms (5x), 100ms (10x)

### 5. Timeline Component (Future)

**Recommendation:** Create as separate component, not integrated into playback controller.

```
PlaybackController
        │
        ▼
Timeline (visual scrubber - reads playback state)
```

The timeline should be a "dumb" visualization that reflects playback state, not a source of truth.

---

## Coupling Concerns for Future Features

### Reverse Playback

| Concern | Mitigation |
|---------|------------|
| FilmStrip already scrolls forward only | Add `scrollDirection` prop to FilmStrip |
| MapCanvas centers on marker | No change needed - just coordinates |
| Data is sorted oldest→newest | Need pre-sorted array for reverse access |

**Verdict:** ✅ Can be added without breaking existing architecture.

### Speed Controls

| Concern | Mitigation |
|---------|------------|
| Interval timer needs variable rate | PlaybackController already accepts configurable interval |
| UI needs speed selector | Add `<SpeedSelector>` component |

**Verdict:** ✅ Minimal coupling - only PlaybackController needs change.

### Timeline Scrubber

| Concern | Mitigation |
|---------|------------|
| Bidirectional sync needed | Timeline → playback, playback → timeline |
| User drag vs playback drag | Add `isDragging` state to prevent conflict |

**Verdict:** ⚠️ Requires careful synchronization protocol design.

### 100k+ Image Support

| Concern | Mitigation |
|---------|------------|
| Loading all thumbnails at once | Virtual scrolling (react-window) in FilmStrip |
| Map marker clustering | Use leaflet.markercluster |
| Memory pressure | Consider pagination + viewport-based loading |

**Verdict:** ⚠️ Requires architectural changes to FilmStrip and MapCanvas.

---

## Conclusion

### Can a single playback controller synchronize filmstrip, map, and selected image?

**✅ YES** - The existing Trace architecture provides all necessary primitives:

1. **FilmStrip** exposes `scrollToThumbnailId` → scrolls to frame
2. **MapCanvas** exposes `centerOnMarkerId` → centers on GPS
3. **TraceView** orchestrates via `selectedDocumentId`

The playback controller simply drives these triggers at timed intervals.

### Architectural Confidence

| Aspect | Confidence | Notes |
|--------|------------|-------|
| Basic playback | **HIGH** | Proven through implementation |
| Reverse playback | **MEDIUM** | Requires sorted array and direction prop |
| Speed controls | **HIGH** | Interval-based, straightforward |
| Timeline | **MEDIUM** | Requires bidirectional sync protocol |
| 100k+ support | **LOW** | Requires virtualization changes |

### Recommended Next Steps

1. **Immediate:** Merge playback controller hook and controls
2. **Short-term:** Add speed controls (interval configuration)
3. **Medium-term:** Design timeline synchronization protocol
4. **Long-term:** Add virtualization for large collections

---

## Files Modified/Created

### Created
- `/dashboard/src/hooks/usePlaybackController.ts` - Playback state machine
- `/dashboard/src/components/PlaybackControls.tsx` - UI controls
- `/dashboard/src/components/PlaybackControls.css` - Styles
- `/refactor/operationplayback/ARCHITECTURAL_SPIKE.md` - This report

### Modified
- `/dashboard/src/pages/TraceView.tsx` - Integrated playback state

---

*This is a proof-of-existence exercise, not a production implementation.*
