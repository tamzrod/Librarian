# Validation Experiments — Operation Playback

## Overview

This document defines experiments needed to validate assumptions before implementation. Each experiment has a clear hypothesis, methodology, and acceptance criteria.

---

## Priority 1 Experiments (Critical Path)

### VT1: User Research on Playback Speed

**Related Assumptions:** A6, OA1, PD1
**Related Risks:** R11
**Priority:** Critical

**Hypothesis:** Users prefer 1 photo/second playback speed as default.

**Methodology:**
1. Create prototype with adjustable playback speed
2. Recruit 10 users with photo collections
3. Ask users to browse using different speeds (0.5x, 1x, 2x)
4. Survey user preference
5. Measure engagement metrics (photos viewed, time spent)

**Variables:**
- Independent: Playback speed (0.5x, 1x, 2x)
- Dependent: User preference, engagement metrics

**Sample Size:** 10 users minimum

**Acceptance Criteria:**
- [ ] ≥60% prefer 1 photo/second OR
- [ ] Clear statistical preference emerges

**Timeline:** 1 week
**Owner:** UX Researcher
**Status:** Not Started

---

### VT2: Marker Clustering Benchmark

**Related Assumptions:** A3, Q9, PD9
**Related Risks:** R3
**Priority:** Critical

**Hypothesis:** Leaflet with marker clustering can handle 500+ markers at 60fps.

**Methodology:**
1. Create test harness with Leaflet
2. Load 100, 500, 1000, 5000, 10000 markers
3. Measure:
   - Initial render time
   - Pan performance (fps)
   - Zoom performance (fps)
   - Memory usage
4. Test with and without clustering
5. Test with Leaflet.markercluster plugin

**Test Data:** Generate random GPS coordinates within bounding box

**Metrics:**
| Metric | Target |
|--------|--------|
| Initial render | < 1s |
| Pan/zoom FPS | ≥ 30fps |
| Memory | < 100MB |

**Acceptance Criteria:**
- [ ] 500 markers: Pass all metrics
- [ ] 1000 markers: Pass with clustering
- [ ] 5000 markers: Pass with clustering, acceptable degradation

**Timeline:** 2 days
**Owner:** Frontend Lead
**Status:** Not Started

---

### VT3: Virtual Scrolling Benchmark

**Related Assumptions:** A4, A18
**Related Risks:** R2
**Priority:** Critical

**Hypothesis:** Virtual scrolling with react-window or @tanstack/react-virtual can handle 100k items at 60fps.

**Methodology:**
1. Create test harness with both libraries
2. Load 1k, 10k, 50k, 100k items
3. Measure:
   - Initial render time
   - Scroll FPS
   - Memory usage
   - DOM node count
4. Compare react-window vs @tanstack/react-virtual
5. Test with horizontal scrolling (filmstrip orientation)

**Test Data:** Array of photo objects with id, thumbnail URL, timestamp

**Metrics:**
| Metric | 1k items | 10k items | 100k items |
|--------|----------|-----------|------------|
| Initial render | < 100ms | < 500ms | < 2s |
| Scroll FPS | 60fps | 60fps | ≥ 30fps |
| Memory | < 50MB | < 100MB | < 500MB |
| DOM nodes | < 100 | < 100 | < 1000 |

**Acceptance Criteria:**
- [ ] 10k items: All metrics pass
- [ ] 100k items: Pass with acceptable degradation
- [ ] Winner identified between libraries

**Timeline:** 3 days
**Owner:** Frontend Lead
**Status:** Not Started

---

### VT4: Synchronization Performance Test

**Related Assumptions:** A5
**Related Risks:** R1
**Priority:** Critical

**Hypothesis:** Synchronization between Map, Filmstrip, and Timeline can complete in < 100ms.

**Methodology:**
1. Create test harness simulating sync scenario
2. Measure time for:
   - Filmstrip click → Map center
   - Map click → Filmstrip scroll
   - Timeline drag → All views update
3. Test with and without debouncing/throttling
4. Measure React render times
5. Identify bottleneck (React, DOM, network)

**Test Data:** 1000 items with GPS coordinates

**Metrics:**
| Scenario | Target |
|----------|--------|
| Filmstrip → Map | < 100ms |
| Map → Filmstrip | < 100ms |
| Timeline → All | < 100ms |

**Acceptance Criteria:**
- [ ] All scenarios complete in < 100ms
- [ ] No feedback loops detected
- [ ] Optimal throttling/debouncing values identified

**Timeline:** 2 days
**Owner:** Frontend Lead
**Status:** Not Started

---

### VT5: Keyboard Shortcut Compatibility

**Related Assumptions:** A6
**Related Risks:** R8
**Priority:** Critical

**Hypothesis:** Proposed keyboard shortcuts don't conflict with major browser/OS shortcuts.

**Methodology:**
1. Review proposed shortcuts:
   - Space: Play/Pause
   - S: Stop
   - R: Toggle Reverse
   - ←/→: Step backward/forward
   - Shift+←/→: Skip 10 frames
   - Home/End: Jump to start/end
   - +/-: Speed adjustment
2. Check conflicts with:
   - Chrome shortcuts
   - Firefox shortcuts
   - Safari shortcuts
   - macOS shortcuts
   - Windows shortcuts
3. Test in browser environment

**Shortcut Conflicts:**
| Shortcut | Chrome | Firefox | Safari | macOS | Windows |
|----------|--------|---------|--------|-------|---------|
| Space | Scroll page | Scroll page | Scroll page | - | - |
| S | Save page | Save page | Save page | Spotlight | Find |
| R | Refresh | Refresh | Refresh | - | Refresh |
| ←/→ | Back/Forward | Back/Forward | Back/Forward | - | Cursor |
| Home/End | Top/Bottom | Top/Bottom | Top/Bottom | Home/End | Top/Bottom |
| +/- | Zoom | Zoom | Zoom | - | - |

**Acceptance Criteria:**
- [ ] No conflicts with browser back/forward
- [ ] Minimal conflicts with other shortcuts
- [ ] Fallback shortcuts defined for conflicts

**Timeline:** 1 day
**Owner:** Frontend Dev
**Status:** Not Started

---

## Priority 2 Experiments (Performance)

### VT6: Playback Animation Benchmark

**Related Assumptions:** A4, A17
**Related Risks:** R5, R6
**Priority:** High

**Hypothesis:** requestAnimationFrame-based playback can achieve 30fps for 100k collections.

**Methodology:**
1. Create playback simulation
2. Measure:
   - Frame timing accuracy
   - Actual FPS achieved
   - Memory usage over time
   - CPU usage
3. Test at different speeds (0.5x, 1x, 2x, 4x)
4. Test with preloading enabled/disabled

**Metrics:**
| Speed | Target FPS | Frame Timing Accuracy |
|-------|------------|----------------------|
| 0.5x | 30fps | 33ms ± 5ms |
| 1x | 30fps | 33ms ± 5ms |
| 2x | 30fps | 33ms ± 5ms |
| 4x | 30fps | 33ms ± 5ms |

**Acceptance Criteria:**
- [ ] 30fps achieved at all speeds
- [ ] No frame drops over 5-minute session
- [ ] Memory stable (no growth)

**Timeline:** 2 days
**Owner:** Frontend Dev
**Status:** Not Started

---

### VT7: Thumbnail Preloading Strategy

**Related Assumptions:** A15, Q8, PD8
**Related Risks:** R6
**Priority:** High

**Hypothesis:** Preloading 10 thumbnails ahead maintains smooth playback.

**Methodology:**
1. Create playback with preloading
2. Test preloading strategies:
   - 5 ahead, 2 behind
   - 10 ahead, 5 behind
   - 20 ahead, 10 behind
3. Measure:
   - Blank frame rate
   - Network bandwidth
   - Memory usage
4. Test with slow network (3G throttling)

**Metrics:**
| Strategy | Blank Frames | Bandwidth | Memory |
|----------|-------------|-----------|--------|
| 5+2 | Baseline | Baseline | Baseline |
| 10+5 | Target | Acceptable | < 200MB |
| 20+10 | Minimal | High | < 500MB |

**Acceptance Criteria:**
- [ ] Blank frame rate < 5%
- [ ] Optimal strategy identified
- [ ] Fallback for slow networks defined

**Timeline:** 2 days
**Owner:** Frontend Dev
**Status:** Not Started

---

### VT8: Memory Leak Detection

**Related Assumptions:** A18
**Related Risks:** R7
**Priority:** High

**Hypothesis:** No memory leaks in playback animation over extended use.

**Methodology:**
1. Create 30-minute playback session simulation
2. Monitor:
   - JS heap size over time
   - DOM node count
   - Event listener count
   - Timer count
3. Test scenarios:
   - Continuous playback (30 min)
   - Start/stop cycling (100 cycles)
   - Filter changes during playback (20 changes)
4. Use Chrome DevTools Memory panel

**Metrics:**
| Metric | Initial | After 30min | Growth |
|--------|---------|-------------|--------|
| Heap size | Baseline | Target < 1.2x | < 20% |
| DOM nodes | < 1000 | < 1100 | < 10% |
| Event listeners | Baseline | Target < 1.1x | < 10% |
| Timers | 0 | Target 0 | 0 |

**Acceptance Criteria:**
- [ ] No significant memory growth
- [ ] All timers cleaned up
- [ ] All event listeners removed

**Timeline:** 1 day
**Owner:** Frontend Dev
**Status:** Not Started

---

### VT9: Timeline Bucket Performance

**Related Assumptions:** Q5, Q6, PD5, PD6
**Priority:** High

**Hypothesis:** Aggregated timeline buckets can display 10 years of data efficiently.

**Methodology:**
1. Create timeline component
2. Generate test data:
   - 100k photos over 10 years
   - Distribution: normal (clustered events)
3. Test bucket strategies:
   - Year buckets
   - Month buckets
   - Week buckets
   - Day buckets
4. Measure:
   - Render time
   - Scroll/zoom responsiveness
   - Memory usage

**Metrics:**
| Zoom Level | Bucket Size | Render Target |
|------------|-------------|--------------|
| Year | Month | < 50ms |
| Month | Week | < 50ms |
| Week | Day | < 50ms |
| Day | Hour | < 100ms |

**Acceptance Criteria:**
- [ ] All zoom levels render in < 100ms
- [ ] Smooth zoom transitions
- [ ] Efficient for 10-year span

**Timeline:** 2 days
**Owner:** Frontend Dev
**Status:** Not Started

---

### VT10: API Pagination Performance

**Related Assumptions:** A2, Q10, PD10
**Related Risks:** R4
**Priority:** High

**Hypothesis:** Cursor-based pagination performs better than offset for large collections.

**Methodology:**
1. Set up pagination test endpoints
2. Test scenarios:
   - First page (limit 200)
   - Page 100 (offset vs cursor)
   - Page 500 (offset vs cursor)
3. Measure:
   - Query execution time
   - Response time
   - Database load
4. Compare keyset vs offset pagination

**Metrics:**
| Query | Offset | Cursor | Winner |
|-------|--------|--------|--------|
| Page 1 | Baseline | Baseline | - |
| Page 100 | < 500ms | < 100ms | Cursor |
| Page 500 | < 1s | < 100ms | Cursor |

**Acceptance Criteria:**
- [ ] Cursor outperforms offset for deep pagination
- [ ] < 100ms for cursor pagination
- [ ] No regression on simple queries

**Timeline:** 2 days
**Owner:** Backend Lead
**Status:** Not Started

---

## Priority 3 Experiments (UX)

### VT11: Mobile Usability Test

**Related Assumptions:** A8
**Related Risks:** R9
**Priority:** Medium

**Hypothesis:** Core playback functionality works on mobile devices.

**Methodology:**
1. Create prototype with mobile layout
2. Test on devices:
   - iPhone 12/13/14 (Safari)
   - Android Chrome
3. Test scenarios:
   - Touch to play/pause
   - Swipe to scrub timeline
   - Tap filmstrip frames
4. Measure:
   - Touch responsiveness
   - Layout correctness
   - Performance (FPS)

**Acceptance Criteria:**
- [ ] All touch interactions work
- [ ] Layout adapts correctly
- [ ] ≥ 24fps on mid-range devices

**Timeline:** 2 days
**Owner:** UX Designer + QA
**Status:** Not Started

---

### VT12: Accessibility Audit

**Related Assumptions:** A6, Q21, Q22, PD23, PD24
**Related Risks:** R10
**Priority:** Medium

**Hypothesis:** Full keyboard and screen reader support is achievable.

**Methodology:**
1. Implement accessibility features
2. Test with:
   - VoiceOver (macOS)
   - NVDA (Windows)
   - Keyboard-only navigation
3. Run automated checks:
   - axe DevTools
   - Lighthouse accessibility
4. Manual testing with disabled users (if available)

**Checklist:**
| Feature | VoiceOver | NVDA | Keyboard |
|---------|-----------|------|----------|
| Playback controls | ✓ | ✓ | ✓ |
| Timeline navigation | ✓ | ✓ | ✓ |
| Filmstrip navigation | ✓ | ✓ | ✓ |
| Status announcements | ✓ | ✓ | N/A |
| Focus management | N/A | N/A | ✓ |

**Acceptance Criteria:**
- [ ] All controls accessible
- [ ] State changes announced
- [ ] No axe violations

**Timeline:** 2 days
**Owner:** QA + Accessibility Specialist
**Status:** Not Started

---

### VT13: Empty/Edge State UX

**Related Assumptions:** Q17, Q18, Q19, PD19, PD20, PD21
**Related Risks:** R11
**Priority:** Medium

**Hypothesis:** Edge cases are handled gracefully with clear UX.

**Methodology:**
1. Test edge cases:
   - Empty collection
   - Single photo
   - Photos without timestamps
   - Photos without GPS
   - Mixed edge cases
2. Evaluate UX for each:
   - Is behavior clear?
   - Is user guided?
   - Are actions available?
3. User testing if possible

**Edge Case Requirements:**
| Case | Requirement |
|------|------------|
| Empty | Clear message + suggestions |
| Single | Static view, no broken controls |
| No timestamps | Grouped separately, visible |
| No GPS | Map graceful, filmstrip normal |

**Acceptance Criteria:**
- [ ] All edge cases have clear UX
- [ ] No broken/disabled controls
- [ ] Users know what to do

**Timeline:** 1 day
**Owner:** UX Designer
**Status:** Not Started

---

## Experiment Summary

| ID | Experiment | Priority | Days | Owner | Status |
|----|-----------|----------|------|-------|--------|
| VT1 | User Research | Critical | 5 | UX Researcher | Not Started |
| VT2 | Marker Clustering | Critical | 2 | Frontend Lead | Not Started |
| VT3 | Virtual Scrolling | Critical | 3 | Frontend Lead | Not Started |
| VT4 | Sync Performance | Critical | 2 | Frontend Lead | Not Started |
| VT5 | Keyboard Shortcuts | Critical | 1 | Frontend Dev | Not Started |
| VT6 | Playback Benchmark | High | 2 | Frontend Dev | Not Started |
| VT7 | Thumbnail Preload | High | 2 | Frontend Dev | Not Started |
| VT8 | Memory Leaks | High | 1 | Frontend Dev | Not Started |
| VT9 | Timeline Buckets | High | 2 | Frontend Dev | Not Started |
| VT10 | API Pagination | High | 2 | Backend Lead | Not Started |
| VT11 | Mobile Usability | Medium | 2 | UX/QA | Not Started |
| VT12 | Accessibility | Medium | 2 | QA/A11y | Not Started |
| VT13 | Edge State UX | Medium | 1 | UX Designer | Not Started |

**Total Days:** 27 (5.4 weeks)
**Critical Path:** VT1, VT2, VT3, VT4, VT5 (13 days)

---

## Dependencies

```
VT1 (User Research)
    │
    └── PD1 (Playback Speed) can be finalized

VT2 (Marker Clustering)
    │
    └── PD9 (Clustering Threshold) can be finalized

VT3 (Virtual Scrolling)
    │
    └── Tech stack decision (react-window vs @tanstack)

VT4 (Sync Performance)
    │
    └── AR10 (Sync Latency) can be verified

VT5 (Keyboard Shortcuts)
    │
    └── A6 (Keyboard Nav) can be verified

VT6 (Playback Benchmark)
    │
    └── A17 (30fps Playback) can be verified

VT7 (Thumbnail Preload)
    │
    └── PD8 (Preload Strategy) can be finalized

VT10 (API Pagination)
    │
    └── A2 (Cursor Pagination) can be verified
```

---

## Experiment Execution Plan

### Week 1
- VT1: User Research (5 days)

### Week 2
- VT2: Marker Clustering (2 days)
- VT5: Keyboard Shortcuts (1 day)

### Week 3
- VT3: Virtual Scrolling (3 days)

### Week 4
- VT4: Sync Performance (2 days)
- VT6: Playback Benchmark (2 days)

### Week 5
- VT7: Thumbnail Preload (2 days)
- VT8: Memory Leaks (1 day)
- VT9: Timeline Buckets (2 days)

### Week 6
- VT10: API Pagination (2 days)
- VT11: Mobile Usability (2 days)

### Week 7
- VT12: Accessibility (2 days)
- VT13: Edge State UX (1 day)

---

## Success Criteria for Validation Phase

- [ ] All Critical experiments pass
- [ ] High priority experiments pass or have mitigation plans
- [ ] All decisions can be finalized based on results
- [ ] Implementation plan can proceed with confidence
