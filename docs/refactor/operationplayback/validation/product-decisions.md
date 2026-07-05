# Product Decisions — Operation Playback

## Overview

This document contains product decisions that require stakeholder input but can be classified as decisions rather than assumptions once made. These are choices about user experience, behavior, and priorities.

---

## Playback Behavior Decisions

### PD1: Default Playback Speed

**Status:** Open Decision → Requires User Research

**Decision Needed:** What should 1x speed represent?

**Options:**
1. 0.5 photos/second — Cinematic, time-lapse feel
2. 1 photo/second — Standard viewing pace
3. 2 photos/second — Efficient browsing

**Input Required:** User research, A/B testing

**Validation Task:** VT1 - User research on playback speed preferences

---

### PD2: Frame Step Definition

**Status:** Open Decision

**Decision Needed:** What does "step one frame" mean?

**Options:**
1. Step = 1 photo (most predictable, recommended)
2. Step = Photos within 1 second of real time
3. Step = 1 cluster of similar photos
4. Step = 1 "event" (AI-detected)

**Recommendation:** Option 1 - Step = 1 photo (most predictable)

---

### PD3: Gap Handling

**Status:** Open Decision

**Decision Needed:** How should playback handle gaps (no photos)?

**Options:**
1. Skip gaps — Jump to next available photo
2. Pause at gaps — Stop and wait for user
3. Show placeholder — "Gap" indicator, auto-continue
4. Compress time — Speed through gaps

**Recommendation:** Option 1 - Skip gaps (video player behavior)

---

### PD4: Photos Without GPS Behavior

**Status:** Open Decision

**Decision Needed:** How should map behave for non-GPS photos?

**Options:**
1. Hide map — Focus entirely on filmstrip
2. Keep last position — Don't move map
3. Show all markers — Highlight current without centering
4. Animate to nearest — Pan to closest GPS photo

**Recommendation:** Option 2 - Keep last map position

---

## Timeline Decisions

### PD5: Timeline Granularity

**Status:** Open Decision

**Decision Needed:** How detailed should timeline be for large collections?

**Options:**
1. Show all photos (cluttered for large sets)
2. Aggregated buckets by zoom level (recommended)
3. Significant moments only (AI-dependent)
4. User-configurable density

**Recommendation:** Option 2 - Zoom-dependent aggregated buckets

---

### PD6: Timeline Zoom Levels

**Status:** Open Decision

**Decision Needed:** What zoom levels should timeline support?

**Options:**
1. Year/Month/Day — 3 levels
2. Year/Month/Week/Day — 4 levels (recommended)
3. Year/Month/Week/Day/Hour — 5 levels
4. Continuous zoom

**Recommendation:** Option 2 - 4 levels (Year/Month/Week/Day)

---

### PD7: Playhead Snap Behavior

**Status:** Open Decision

**Decision Needed:** Should playhead snap or be free?

**Options:**
1. Snap to photos — Always on a photo
2. Free movement — Can be anywhere
3. Hybrid — Snap when playing, free when scrubbing (recommended)

**Recommendation:** Option 3 - Snap when playing, free when scrubbing

---

## Performance Decisions

### PD8: Preloading Strategy

**Status:** Open Decision

**Decision Needed:** How aggressively to preload thumbnails?

**Options:**
1. Minimal — Only adjacent
2. Moderate — 10 ahead, 5 behind (recommended)
3. Aggressive — 50 ahead, 25 behind
4. Adaptive — Based on connection speed

**Recommendation:** Option 2 - Moderate preload

---

### PD9: Marker Clustering Threshold

**Status:** Open Decision

**Decision Needed:** When to switch from markers to clusters?

**Options:**
1. 100 markers — Aggressive
2. 500 markers — Balanced (recommended)
3. 1000 markers — Minimal
4. Adaptive — Based on zoom and screen

**Recommendation:** Option 2 - 500 markers max

**Validation Task:** VT2 - Benchmark clustering at different thresholds

---

### PD10: Pagination Strategy

**Status:** Open Decision

**Decision Needed:** How to handle 100k+ collections?

**Options:**
1. Client-side cursor pagination
2. Server-side windowing
3. Hybrid with summary endpoint (recommended)
4. Pre-computed buckets

**Recommendation:** Option 3 - Hybrid with timeline summary endpoint

---

## User Interface Decisions

### PD11: Playback Controls Placement

**Status:** Open Decision

**Decision Needed:** Where to position playback controls?

**Options:**
1. Top bar — Always visible (recommended)
2. Bottom overlay — Floating
3. Inline with timeline
4. User-repositionable

**Recommendation:** Option 1 - Top bar (media player convention)

---

### PD12: Hover Preview Delay

**Status:** Open Decision

**Decision Needed:** How long before preview appears on hover?

**Options:**
1. 100ms — Instant feel
2. 200ms — Prevents accidental triggers (recommended)
3. 300ms — More deliberate
4. User-configurable

**Recommendation:** Option 2 - 200ms delay

---

### PD13: Filmstrip Default Size

**Status:** Open Decision

**Decision Needed:** What should default filmstrip height be?

**Options:**
1. 120px — Current compact
2. 180px — Moderate expansion (recommended)
3. 240px — Large, cinematic
4. User-configurable

**Recommendation:** Option 2 - 180px default, 240px expanded

---

### PD14: View Mode Persistence

**Status:** Open Decision

**Decision Needed:** Should playback mode persist across sessions?

**Options:**
1. Always on — No option to disable
2. localStorage — Remember user's choice (recommended)
3. URL — Shareable state
4. Per-session — Reset each visit

**Recommendation:** Option 2 - localStorage with URL override

---

### PD15: Playback Controls Visibility

**Status:** Open Decision

**Decision Needed:** Should playback controls be visible by default?

**Options:**
1. Always visible — Always shown (recommended)
2. Show on hover — Appear when mouse near
3. Show on first use — Visible until first interaction
4. Toggle button — Hidden behind button

**Recommendation:** Option 1 - Always visible

---

## Filter System Decisions

### PD16: Years Filter Replacement

**Status:** Open Decision

**Decision Needed:** How to handle year selection without years filter?

**Options:**
1. Remove entirely — Timeline only (recommended)
2. Keep secondary — Less prominent
3. Convert to timeline selection
4. Both options

**Recommendation:** Option 1 - Remove entirely, timeline is source of truth

---

### PD17: Filter Presets

**Status:** Open Decision

**Decision Needed:** Should filter presets be supported?

**Options:**
1. Not in MVP — Add later
2. Simple localStorage — Personal presets (recommended)
3. Full cloud sync — Cross-device
4. Shared presets — Team/organization

**Recommendation:** Option 2 - localStorage in MVP

---

### PD18: Event Stream Replacement

**Status:** Open Decision

**Decision Needed:** What replaces the EventStream?

**Options:**
1. Timeline X-axis — Primary event display (recommended)
2. Expanded filmstrip — More prominent thumbnails
3. Hybrid — Timeline + expanded filmstrip
4. Side panel — Collapsible detail view

**Recommendation:** Option 1 - Timeline X-axis

---

## Edge Case Decisions

### PD19: Empty Collection

**Status:** Open Decision

**Decision Needed:** What to show when no photos match filters?

**Options:**
1. Empty state message — "No photos found"
2. Suggestion UI — "Try widening filters" (recommended)
3. Auto-relaxation — Automatically expand filters
4. Import prompt — "Add photos to get started"

**Recommendation:** Option 2 - Empty state with suggestions

---

### PD20: Single Photo Behavior

**Status:** Open Decision

**Decision Needed:** How should playback work with only one photo?

**Options:**
1. Static view — No playback controls (recommended)
2. Controls disabled — Visible but not functional
3. Single photo mode — Adapted UI
4. Navigate to detail — Open photo detail view

**Recommendation:** Option 1 - Static view, disable playback

---

### PD21: Missing Timestamp Handling

**Status:** Open Decision

**Decision Needed:** Where to place photos without timestamps?

**Options:**
1. Exclude from playback — Only in detail view (recommended)
2. Place at end — Cluster at timeline end
3. Place at beginning — Cluster at timeline start
4. Show warning — Highlight as data issue

**Recommendation:** Option 1 - Exclude from playback

---

### PD22: Rapid Interaction Handling

**Status:** Open Decision

**Decision Needed:** How to handle rapid timeline scrubbing?

**Options:**
1. Debounce — Update after user stops
2. Throttle — Reduced update rate (recommended)
3. Immediate — Always show current position
4. Preview mode — Show thumbnails during scrub

**Recommendation:** Option 2 - Throttle to 60fps, thumbnails after settle

---

## Accessibility Decisions

### PD23: Screen Reader Level

**Status:** Open Decision

**Decision Needed:** What level of screen reader support?

**Options:**
1. Basic — Announce current photo
2. Full — Complete navigation announcements (recommended)
3. Separate mode — Simplified accessible version
4. Progressive — Improve as we go

**Recommendation:** Option 2 - Full support from start

---

### PD24: Keyboard Shortcut Scope

**Status:** Open Decision

**Decision Needed:** How comprehensive should keyboard nav be?

**Options:**
1. Essential only — Play/pause, step
2. Standard media keys — Full transport controls (recommended)
3. All controls — Every action keyboard-accessible
4. Vim-style — hjkl navigation

**Recommendation:** Option 2 - Standard media keys

---

## Feature Scope Decisions

### PD25: Video Export

**Status:** Future Decision

**Decision Needed:** Should playback be exportable as video?

**Options:**
1. Not planned — Out of scope forever
2. Future consideration — Add later
3. In roadmap — Planned post-MVP
4. Research needed — Investigate feasibility

**Current Stance:** Option 2 - Future consideration only

---

### PD26: Collaborative Playback

**Status:** Future Decision

**Decision Needed:** Should playback be shareable?

**Options:**
1. Not planned — Single-user only
2. Share link — Share position/filter (recommended future)
3. Live sync — Multiple users same session
4. Annotations — Comments visible to others

**Current Stance:** Option 2 - Share link in future versions

---

### PD27: AI Integration

**Status:** Future Decision

**Decision Needed:** Should AI power any features?

**Options:**
1. None — Pure chronological playback
2. Smart clustering — Group similar moments
3. Auto-captions — AI-generated descriptions
4. Highlight reel — AI-curated best moments

**Current Stance:** Option 2 - Smart clustering (P16 Phase 3)

---

## Decisions Made (Preliminary Recommendations)

For decisions where no strong justification exists for alternatives, the following are recommended as default choices unless user research indicates otherwise:

| ID | Decision | Recommendation | Confidence |
|----|----------|----------------|------------|
| PD2 | Frame step | 1 photo | High |
| PD3 | Gap handling | Skip | High |
| PD5 | Timeline granularity | Zoom buckets | High |
| PD6 | Zoom levels | 4 levels | Medium |
| PD7 | Playhead snap | Hybrid | High |
| PD9 | Clustering threshold | 500 markers | Medium |
| PD11 | Controls placement | Top bar | High |
| PD12 | Hover delay | 200ms | Medium |
| PD16 | Years filter | Remove | High |
| PD17 | Filter presets | localStorage | High |
| PD19 | Empty collection | Suggestions | High |
| PD20 | Single photo | Static view | High |
| PD21 | Missing timestamp | Exclude | High |
| PD23 | Screen reader | Full support | High |

**Note:** These are recommendations, not requirements. User research may override.

---

## Input Required From

| Stakeholder | Decisions Needed |
|-------------|----------------|
| Product Manager | PD1, PD14, PD16, PD17, PD25, PD26 |
| UX Designer | PD5, PD6, PD7, PD11, PD12, PD13, PD19, PD23 |
| User Research | PD1, PD2, PD8, PD9 |
| Engineering Lead | PD8, PD9, PD10, PD22 |
| Accessibility Specialist | PD23, PD24 |
| Leadership | PD25, PD26, PD27 |

---

## Summary

| Category | Decisions | Made | Pending |
|----------|-----------|------|---------|
| Playback Behavior | 4 | 0 | 4 |
| Timeline | 3 | 0 | 3 |
| Performance | 3 | 0 | 3 |
| User Interface | 5 | 0 | 5 |
| Filter System | 3 | 0 | 3 |
| Edge Cases | 4 | 0 | 4 |
| Accessibility | 2 | 0 | 2 |
| Feature Scope | 3 | 0 | 3 |
| **Total** | **27** | **0** | **27** |

**Recommendation:** Schedule product review to finalize high-priority decisions before implementation begins.
