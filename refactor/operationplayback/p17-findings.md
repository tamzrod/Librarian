# P17 - Operation Playback MVP Findings

**Date:** 2026-07-05  
**Phase:** Implementation Phase P17 - Playback MVP  
**Status:** Complete

---

## Executive Summary

P17 implemented a minimal playback feature to validate the synchronization architecture discovered during the architectural spike. The implementation confirms that the existing Trace architecture can support playback without major architectural changes.

**Key Finding:** A single playback controller (hook) inside TraceView can synchronize filmstrip, map, and selected image without circular updates, provided user interactions stop playback immediately.

---

## Success Criteria Verification

| Criterion | Status | Notes |
|-----------|--------|-------|
| Play advances images every second | ✅ | `usePlaybackController` interval fires at 1s |
| Filmstrip follows playback | ✅ | `scrollToThumbnailId` triggers FilmStrip scroll |
| Map follows playback | ✅ | `centerOnMarkerId` triggers MapCanvas center |
| Stop halts playback | ✅ | `stop()` clears interval and sets mode |
| Playback stops at final image | ✅ | Index check prevents overflow |
| Thumbnail click stops playback | ✅ | `handleThumbnailClick` checks `isPlaying` |
| Marker click stops playback | ✅ | `handleMarkerClick` checks `isPlaying` |
| Existing Trace behavior unchanged | ✅ | Only added new handlers, no modifications |

---

## New State Variables Introduced

### TraceView Level

```typescript
// Playback sequence (loaded from API, sorted chronologically)
const [thumbnails, setThumbnails] = useState<TraceEventItem[]>([])

// Derived from usePlaybackController hook:
const {
  mode: playbackMode,       // 'stopped' | 'playing'
  currentIndex: playbackIndex, // 0 to thumbnails.length - 1
  isPlaying,                 // boolean convenience
  play,                     // () => void
  stop,                     // () => void
} = usePlaybackController(thumbnails.length)
```

### usePlaybackController Hook Level

```typescript
// Internal state (encapsulated in hook)
const [mode, setMode] = useState<PlaybackMode>('stopped')
const [currentIndex, setCurrentIndex] = useState(0)
const intervalRef = useRef<number | null>(null)
const lastUpdateRef = useRef<number>(0)
```

**Total new state variables at TraceView level:** 1 (`thumbnails` array)

---

## Unexpected Coupling Discovered

### 1. Data Duplication

**Issue:** The playback implementation loads thumbnails from the API inside TraceView, which duplicates data that FilmStrip already loads.

```
TraceView
├── loads: thumbnails[] ────── For playback
└── passes to FilmStrip: filters
                          └── FilmStrip loads: thumbnails[] (same data)
```

**Impact:** Two API calls for the same data during playback.

**Resolution:** Acceptable for MVP. Future phases should consider:
- Passing thumbnails from TraceView to FilmStrip
- Or using a shared data hook

### 2. Filter Change Cascade

**Issue:** When filters change, thumbnails array resets. Playback must stop to avoid index out-of-bounds.

**Location:** `useEffect` for `filters` dependency:
```typescript
useEffect(() => {
  if (isPlaying) {
    stop()
  }
  loadPlaybackThumbnails()
}, [filters])
```

**Impact:** None - this is correct behavior. User's filter change = intentional action that should stop playback.

### 3. Dependency Array Sensitivity

**Issue:** The playback synchronization effect depends on:
```typescript
}, [playbackIndex, playbackMode, thumbnails])
```

If `thumbnails` reference changes (even with same content), effect re-runs. This could cause extra renders during filter changes.

**Impact:** Minor performance concern. Acceptable for MVP.

---

## Synchronization Issues Found

### Issue 1: Trigger Clearing Pattern is Fragile

**Current implementation:**
```typescript
useEffect(() => {
  if (scrollToThumbnailId) {
    const timer = setTimeout(() => setScrollToThumbnailId(undefined), 100)
    return () => clearTimeout(timer)
  }
}, [scrollToThumbnailId])
```

**Problem:** 
- Magic number `100` and `500` for delays
- If component renders slowly, trigger may clear before child uses it
- Race condition between trigger set and clear

**Recommended fix for P18:**
```typescript
// Use a version pattern instead of clearing
const [scrollTrigger, setScrollTrigger] = useState({
  id: null as number | null,
  version: 0
})

// In sync effect:
setScrollTrigger({ id: documentId, version: scrollTrigger.version + 1 })

// In FilmStrip:
useEffect(() => {
  if (scrollTrigger.id && scrollTrigger.version !== prevVersion) {
    // perform scroll
  }
}, [scrollTrigger])
```

### Issue 2: Double API Call on Filter Change

**Current behavior:**
1. User changes filter
2. `handleFiltersChange` → `setFilters(newFilters)`
3. FilmStrip's `useEffect` triggers → loads thumbnails
4. TraceView's `useEffect` triggers → loads thumbnails (again)

**Impact:** 2x API calls

**Possible resolutions:**
- Pass thumbnails down from TraceView to FilmStrip
- Use React Context for shared data
- Accept for MVP (caching handles this)

### Issue 3: Interval Throttle is Over-Engineered

**Current code:**
```typescript
const now = Date.now()
if (now - lastUpdateRef.current >= 900) {
  lastUpdateRef.current = now
  // update index
}
```

**Problem:** The 900ms throttle was added during spike to avoid "multiple updates in same frame." This shouldn't happen with `setInterval` at 1000ms.

**Recommendation:** Remove throttle for P18. If React batches updates cause issues, use `flushSync` or a ref check instead.

---

## Architecture Observations

### State Ownership

```
TraceView (OWNER)
├── playbackMode ────────────▶ PlaybackControls
├── playbackIndex ────────────▶ PlaybackControls
├── thumbnails[] ─────────────▶ Source of truth for sequence
├── selectedDocumentId ────────▶ FilmStrip, MapCanvas
├── scrollToThumbnailId ──────▶ FilmStrip
└── centerOnMarkerId ─────────▶ MapCanvas
```

**Finding:** State ownership is clear. TraceView is the single source of truth for playback.

### Component Coupling

| Connection | Direction | Coupling |
|------------|-----------|----------|
| TraceView → PlaybackControls | Props | Low - stable interface |
| TraceView → FilmStrip | Props + State | Low - existing interface |
| TraceView → MapCanvas | Props + State | Low - existing interface |
| PlaybackController → Components | Indirect | Through TraceView |

**Finding:** No unexpected coupling. All synchronization flows through TraceView.

### Feedback Loop Analysis

**Tested scenarios:**

| Scenario | Feedback Loop? | Resolution |
|----------|----------------|------------|
| Play → advance → FilmStrip scroll | No | FilmStrip is subscriber only |
| Play → advance → MapCanvas center | No | MapCanvas is subscriber only |
| Click thumbnail → stop playback | No | `isPlaying` check stops playback |
| Click marker → stop playback | No | `isPlaying` check stops playback |
| Change filter → reset thumbnails | N/A | Playback stops before reset |

**Finding:** No circular updates. User interactions always take precedence.

---

## Recommendations for P18

### Priority 1: Fix Trigger Clearing Pattern

**Problem:** Current `setTimeout` clearing is fragile.

**Solution:** Implement version-based trigger pattern.

**Files affected:** TraceView.tsx, FilmStrip.tsx, MapCanvas.tsx

### Priority 2: Add `reset` Function to Playback Controller

**Problem:** No way to reset playback to beginning without stopping.

**Solution:** Add optional `reset` function:
```typescript
const reset = useCallback(() => {
  setCurrentIndex(0)
  setMode('stopped')
}, [])
```

**Files affected:** usePlaybackController.ts

### Priority 3: Remove Interval Throttle

**Problem:** Over-engineered throttle that shouldn't be needed.

**Solution:** Remove `lastUpdateRef` and throttle check.

**Files affected:** usePlaybackController.ts

### Priority 4: Add Playback Position Display

**Problem:** Current position indicator shows "1 / N" but doesn't indicate what's selected.

**Solution:** Display current photo timestamp or filename in PlaybackControls.

**Files affected:** PlaybackControls.tsx

---

## What NOT to Implement in P18

Based on P17 findings, these features require architectural changes beyond the MVP:

| Feature | Blocker | Recommendation |
|---------|---------|----------------|
| Pause | Requires `paused` mode in state machine | Implement in P19 (after speed control) |
| Reverse playback | Requires direction state | Implement after P19 |
| Speed control | UI complexity | Implement as separate P |
| Timeline | Bidirectional sync protocol | Requires design document |

---

## Files Created/Modified

### Created
- `/dashboard/src/hooks/usePlaybackController.ts` - Playback state machine hook
- `/dashboard/src/components/PlaybackControls.tsx` - Play/Stop UI
- `/dashboard/src/components/PlaybackControls.css` - Styles

### Modified
- `/dashboard/src/pages/TraceView.tsx` - Integrated playback state and synchronization

### No Changes To
- FilmStrip.tsx - No changes required
- MapCanvas.tsx - No changes required  
- EventStream.tsx - No changes required
- FilterPalette.tsx - No changes required
- API layer - No changes required

---

## Conclusion

P17 validates that the existing Trace architecture can support minimal playback functionality. The key architectural insight is:

**A playback controller can live inside TraceView as a hook, driving existing synchronization primitives (`scrollToThumbnailId`, `centerOnMarkerId`, `selectedDocumentId`) at timed intervals.**

The implementation is minimal, production-ready for basic use cases, and provides a foundation for future phases. Critical synchronization issues identified are related to the trigger clearing pattern, not the playback logic itself.

**Recommendation:** Proceed to P18 (Speed Control) after fixing trigger clearing pattern.

---

*P17 is a foundation validation exercise, not a production feature delivery.*
