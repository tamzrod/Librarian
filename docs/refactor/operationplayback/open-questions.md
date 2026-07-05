# Open Questions — Operation Playback

## Overview

This document captures open questions that need to be resolved before or during Operation Playback implementation. Questions are categorized by area and prioritized for decision-making.

---

## Playback Behavior

### Q1: Default Playback Speed

**Question:** What should the default playback speed be?

**Options:**
1. 0.5 photos/second — Slow, cinematic (like time-lapse)
2. 1 photo/second — Standard viewing pace
3. 2 photos/second — Fast, efficient browsing
4. User-configurable — Remember last used speed

**Current Thinking:** 1 photo/second (1x speed)

**Decision Needed By:** Phase 4 (Playback Controls)

---

### Q2: Frame Step Definition

**Question:** What does "step one frame" mean?

**Options:**
1. Step = 1 photo
2. Step = Photos within 1 second of real time (may skip multiple)
3. Step = 1 cluster of similar photos (same location/time)
4. Step = 1 "event" (AI-detected significant moment)

**Current Thinking:** Step = 1 photo (most predictable, lowest complexity)

**Decision Needed By:** Phase 5 (Playback Engine)

---

### Q3: Gap Handling

**Question:** How should playback handle gaps in the timeline (periods with no photos)?

**Options:**
1. Skip gaps — Jump to next available photo
2. Pause at gaps — Stop and wait for user to continue
3. Show placeholder — Display "gap" indicator, auto-continue
4. Compress time — Speed through gaps quickly

**Current Thinking:** Skip gaps (similar to video player behavior)

**Decision Needed By:** Phase 5 (Playback Engine)

---

### Q4: Photos Without GPS

**Question:** How should the map behave during playback when the current photo has no GPS data?

**Options:**
1. Hide map — Focus entirely on filmstrip
2. Keep last position — Don't move map, show indicator
3. Show all visible markers — Highlight current without centering
4. Animate to nearest — Pan to closest photo with GPS

**Current Thinking:** Keep last position, show indicator

**Decision Needed By:** Phase 5 (Playback Engine)

---

## Timeline

### Q5: Timeline Granularity

**Question:** How detailed should the timeline be for large collections?

**Options:**
1. Show all photos — Fine granularity, clutter for large collections
2. Aggregated buckets — Day/week/month based on zoom
3. Significant moments only — AI-detected highlights
4. User-configurable density — Let users choose

**Current Thinking:** Zoom-dependent aggregated buckets

**Decision Needed By:** Phase 2 (Timeline X-axis)

---

### Q6: Timeline Zoom Levels

**Question:** What zoom levels should the timeline support?

**Options:**
1. Year/Month/Day only — 3 levels
2. Year/Month/Week/Day — 4 levels
3. Year/Month/Week/Day/Hour — 5 levels
4. Continuous zoom — Infinite granularity

**Current Thinking:** Year/Month/Week/Day (4 levels)

**Decision Needed By:** Phase 2 (Timeline X-axis)

---

### Q7: Playhead Snap Behavior

**Question:** Should the playhead snap to individual photos or stay continuous?

**Options:**
1. Snap to photos — Playhead always on a photo
2. Free movement — Playhead can be anywhere on timeline
3. Snap when playing, free when scrubbing

**Current Thinking:** Snap when playing, free when scrubbing

**Decision Needed By:** Phase 2 (Timeline X-axis)

---

## Performance

### Q8: Preloading Strategy

**Question:** How aggressively should we preload thumbnails during playback?

**Options:**
1. Minimal — Only preload immediately adjacent
2. Moderate — Preload 10 ahead, 5 behind
3. Aggressive — Preload 50 ahead, 25 behind
4. Adaptive — Adjust based on connection speed

**Current Thinking:** Moderate (10 ahead, 5 behind)

**Decision Needed By:** Phase 5 (Playback Engine)

---

### Q9: Marker Clustering Threshold

**Question:** At what number of visible markers should we switch to clusters?

**Options:**
1. 100 markers — Aggressive clustering
2. 500 markers — Balanced clustering
3. 1000 markers — Minimal clustering
4. Adaptive — Based on zoom level and screen size

**Current Thinking:** 500 markers max visible

**Decision Needed By:** Phase 1 (Scalability)

---

### Q10: Large Collection Pagination

**Question:** How should the API handle collections over 100k photos?

**Options:**
1. Client-side cursor pagination — Load as user scrolls
2. Server-side windowing — API returns visible range + buffer
3. Hybrid — Summary + detail on demand
4. Denormalize timeline data — Pre-compute buckets

**Current Thinking:** Hybrid approach with timeline summary endpoint

**Decision Needed By:** Phase 1 (Scalability)

---

## User Interface

### Q11: Playback Controls Placement

**Question:** Where should the playback controls be positioned?

**Options:**
1. Top bar — Below header, always visible
2. Bottom overlay — Floating over timeline
3. Inline with timeline — Part of timeline component
4. Floating — Can be repositioned by user

**Current Thinking:** Top bar (consistent with media players)

**Decision Needed By:** Phase 4 (Playback Controls)

---

### Q12: Hover Preview Delay

**Question:** How long should the user hover before showing preview?

**Options:**
1. 100ms — Instant feel
2. 200ms — Prevents accidental triggers
3. 300ms — More deliberate
4. User-configurable — Let users choose

**Current Thinking:** 200ms delay

**Decision Needed By:** Phase 6 (Hover Previews)

---

### Q13: Filmstrip Default Size

**Question:** What should the default filmstrip height be?

**Options:**
1. 120px (current) — Compact, information-dense
2. 180px — Moderate expansion
3. 240px — Large, cinematic
4. User-configurable — Remember preference

**Current Thinking:** 180px default, expandable to 240px

**Decision Needed By:** Phase 8 (Filmstrip Expansion)

---

### Q14: View Mode Persistence

**Question:** Should the Operation Playback mode persist across sessions?

**Options:**
1. Always on — Operation Playback is the only mode
2. Persist to localStorage — Remember user's choice
3. Persist to URL — Shareable state
4. Per-session — Reset on each visit

**Current Thinking:** Persist to localStorage with URL override

**Decision Needed By:** Phase 4 (Playback Controls)

---

## Filter System

### Q15: Years Filter Replacement

**Question:** Should years be selectable in the timeline or removed entirely?

**Options:**
1. Remove entirely — Timeline is the only time selector
2. Keep as secondary — Visible but less prominent
3. Convert to timeline selection — Select year on timeline
4. Both options — Years in filter + timeline selection

**Current Thinking:** Remove entirely, timeline is the source of truth

**Decision Needed By:** Phase 9 (Cleanup)

---

### Q16: Filter Presets

**Question:** Should Operation Playback support saved filter presets?

**Options:**
1. Not in MVP — Add later
2. Simple localStorage — Save/load personal presets
3. Full cloud sync — Presets available across devices
4. Shared presets — Team/organization presets

**Current Thinking:** Simple localStorage in MVP, cloud sync later

**Decision Needed By:** Phase 9 (Cleanup)

---

## Edge Cases

### Q17: Empty Collection

**Question:** What UI should be shown when there are no photos matching filters?

**Options:**
1. Empty state message — "No photos found"
2. Suggestion UI — "Try widening your filters"
3. Automatic relaxation — Auto-expand filters
4. Import prompt — "Add photos to get started"

**Current Thinking:** Empty state with suggestions

**Decision Needed By:** Phase 0 (Foundation)

---

### Q18: Single Photo

**Question:** How should playback behave with only one photo?

**Options:**
1. Show static view — No playback controls visible
2. Show controls disabled — Controls visible but not functional
3. Show single photo mode — Adapted UI for single item
4. Navigate to detail — Open photo detail view

**Current Thinking:** Show static view (disable playback)

**Decision Needed By:** Phase 5 (Playback Engine)

---

### Q19: Photos Without Timestamps

**Question:** How should photos with missing timestamps be handled?

**Options:**
1. Exclude from playback — Only timestamped photos
2. Place at end — Cluster at timeline end
3. Place at beginning — Cluster at timeline start
4. Show warning — Highlight as data issue

**Current Thinking:** Exclude from playback, show in detail view only

**Decision Needed By:** Phase 5 (Playback Engine)

---

### Q20: Rapid User Interaction

**Question:** How should the system handle rapid scrubbing (user drags timeline quickly)?

**Options:**
1. Debounce updates — Update UI after user stops
2. Throttle updates — Update at reduced rate
3. Immediate updates — Always show current position
4. Preview mode — Show thumbnail previews during scrub

**Current Thinking:** Throttle updates to 60fps max, load thumbnails after settle

**Decision Needed By:** Phase 3 (Synchronization)

---

## Accessibility

### Q21: Screen Reader Support

**Question:** What level of screen reader support is required?

**Options:**
1. Basic — Announce current photo on change
2. Full — Full navigation and status announcements
3. Separate accessible mode — Simplified UI for a11y
4. Progressive enhancement — Improve as we go

**Current Thinking:** Full support from the start

**Decision Needed By:** Phase 4 (Playback Controls)

---

### Q22: Keyboard Navigation Scope

**Question:** Should all playback controls be keyboard-accessible?

**Options:**
1. Essential only — Play/pause, step
2. Standard media keys — Full transport controls
3. All controls — Every action keyboard-accessible
4. Vim-style — hjkl for navigation

**Current Thinking:** Standard media keys + essential shortcuts

**Decision Needed By:** Phase 4 (Playback Controls)

---

## Future Considerations

### Q23: Video Export

**Question:** Should Operation Playback eventually support exporting playback as video?

**Options:**
1. Not planned — Out of scope forever
2. Future consideration — Potentially add later
3. In roadmap — Planned for post-MVP
4. Research needed — Investigate feasibility

**Current Thinking:** Future consideration

**Decision Needed By:** Not required for MVP

---

### Q24: Collaborative Playback

**Question:** Should playback sessions be shareable for collaboration?

**Options:**
1. Not planned — Single-user experience
2. Share link — Share current position/filter
3. Live sync — Multiple users same session
4. Annotation sharing — Comments visible to others

**Current Thinking:** Share link in future versions

**Decision Needed By:** Not required for MVP

---

### Q25: AI Integration

**Question:** Should Operation Playback integrate AI for smart features?

**Options:**
1. None — Pure chronological playback
2. Smart clustering — Group similar moments
3. Auto-captions — AI-generated descriptions
4. Highlight reel — AI-curated best moments

**Current Thinking:** Smart clustering as part of P16 Phase 3

**Decision Needed By:** P16 Phase 3 planning

---

## Decision Log

| Question | Decision | Date | Decider | Notes |
|----------|----------|------|---------|-------|
| Q1 | 1 photo/second | TBD | | |
| Q2 | 1 photo per step | TBD | | |
| Q3 | Skip gaps | TBD | | |
| Q4 | Keep last map position | TBD | | |
| Q5 | Zoom-dependent buckets | TBD | | |
| Q6 | 4 zoom levels | TBD | | |
| Q7 | Snap when playing, free when scrubbing | TBD | | |
| Q8 | Moderate preload (10 ahead, 5 behind) | TBD | | |
| Q9 | 500 markers max | TBD | | |
| Q10 | Hybrid with summary endpoint | TBD | | |
| Q11 | Top bar | TBD | | |
| Q12 | 200ms delay | TBD | | |
| Q13 | 180px default, 240px expanded | TBD | | |
| Q14 | localStorage + URL override | TBD | | |
| Q15 | Remove entirely | TBD | | |
| Q16 | localStorage in MVP | TBD | | |
| Q17 | Empty state with suggestions | TBD | | |
| Q18 | Disable playback | TBD | | |
| Q19 | Exclude from playback | TBD | | |
| Q20 | Throttle to 60fps | TBD | | |
| Q21 | Full support from start | TBD | | |
| Q22 | Standard media keys | TBD | | |
| Q23 | Future consideration | TBD | | |
| Q24 | Share link future | TBD | | |
| Q25 | Smart clustering P16 Phase 3 | TBD | | |

---

## Prioritization for Decisions

### Must Decide Before Phase 1 (Scalability)
- Q9: Marker clustering threshold
- Q10: Pagination strategy

### Must Decide Before Phase 2 (Timeline)
- Q5: Timeline granularity
- Q6: Zoom levels
- Q7: Snap behavior

### Must Decide Before Phase 4 (Controls)
- Q1: Default speed
- Q11: Controls placement
- Q14: Mode persistence

### Must Decide Before Phase 5 (Engine)
- Q2: Step definition
- Q3: Gap handling
- Q4: GPS handling
- Q8: Preloading strategy
- Q18: Single photo handling
- Q19: Missing timestamp handling

### Must Decide Before Phase 6 (Hover)
- Q12: Hover delay

### Must Decide Before Phase 8 (Filmstrip)
- Q13: Default size

### Must Decide Before Phase 9 (Cleanup)
- Q15: Years filter removal
- Q16: Filter presets
- Q17: Empty collection UI

### Can Decide Anytime
- Q20: Rapid interaction
- Q21-Q22: Accessibility
- Q23-Q25: Future features

---

## Help Wanted

These questions require input from:

| Question | Input Needed From |
|----------|------------------|
| Q1, Q2, Q3 | Product Manager, UX Research |
| Q4, Q5, Q6 | UX Designer |
| Q8, Q9, Q10 | Backend/Frontend Lead |
| Q11, Q12, Q13 | UX Designer, Frontend |
| Q14, Q15, Q16 | Product Manager |
| Q17, Q18, Q19 | UX Designer, Product |
| Q20 | Frontend Lead |
| Q21, Q22 | Accessibility Specialist |
| Q23-Q25 | Product Manager, Leadership |
