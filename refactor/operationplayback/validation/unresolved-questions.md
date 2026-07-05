# Unresolved Questions — Operation Playback

## Overview

This document tracks questions that remain open after classification of assumptions. These are questions that need stakeholder input, further research, or validation experiments to resolve.

---

## Questions Pending Product Decision

### UQ1: Default Playback Speed

**Status:** Pending user research

**Question:** What should 1x playback speed be?

**Options:**
- 0.5 photos/second (cinematic)
- 1 photo/second (standard)
- 2 photos/second (fast)

**Blocked By:** VT1 (User Research)
**Decision Needed:** Phase 4
**Priority:** High

---

### UQ2: View Mode Persistence

**Status:** Pending product decision

**Question:** Should playback mode persist across sessions?

**Options:**
- Always on (no disable)
- localStorage (remember choice)
- URL (shareable)
- Per-session (reset)

**Decision Needed:** Phase 4
**Priority:** Medium

---

### UQ3: Filter Presets

**Status:** Pending product decision

**Question:** Should saved filter presets be supported?

**Options:**
- Not in MVP
- Simple localStorage
- Cloud sync

**Decision Needed:** Phase 9
**Priority:** Low (MVP deferrable)

---

### UQ4: Video Export

**Status:** Future consideration

**Question:** Should playback be exportable as video?

**Options:**
- Not planned
- Future consideration
- In roadmap

**Decision Needed:** Post-MVP
**Priority:** Low

---

### UQ5: Collaborative Playback

**Status:** Future consideration

**Question:** Should playback be shareable with others?

**Options:**
- Single-user only
- Share link
- Live sync
- Annotations

**Decision Needed:** Post-MVP
**Priority:** Low

---

### UQ6: AI Integration

**Status:** Pending P16 Phase 3

**Question:** Should AI power smart features?

**Options:**
- None (pure chronological)
- Smart clustering
- Auto-captions
- Highlight reel

**Decision Needed:** P16 Phase 3 planning
**Priority:** Low

---

## Questions Pending Technical Validation

### UQ7: Preloading Strategy

**Status:** Pending VT7

**Question:** How aggressively to preload thumbnails?

**Options:**
- Minimal (adjacent only)
- Moderate (10 ahead, 5 behind)
- Aggressive (50 ahead, 25 behind)
- Adaptive

**Blocked By:** VT7 (Thumbnail Preloading)
**Decision Needed:** Phase 5
**Priority:** Medium

---

### UQ8: Marker Clustering Threshold

**Status:** Pending VT2

**Question:** When to switch from markers to clusters?

**Options:**
- 100 markers
- 500 markers
- 1000 markers
- Adaptive

**Blocked By:** VT2 (Marker Clustering Benchmark)
**Decision Needed:** Phase 1
**Priority:** High

---

### UQ9: Pagination Strategy

**Status:** Pending VT10

**Question:** How to handle 100k+ collections?

**Options:**
- Client-side cursor
- Server-side windowing
- Hybrid with summary
- Pre-computed buckets

**Blocked By:** VT10 (API Pagination)
**Decision Needed:** Phase 1
**Priority:** High

---

### UQ10: Timeline Zoom Levels

**Status:** Pending design validation

**Question:** What zoom levels should timeline support?

**Options:**
- Year/Month/Day (3 levels)
- Year/Month/Week/Day (4 levels)
- Year/Month/Week/Day/Hour (5 levels)
- Continuous

**Decision Needed:** Phase 2
**Priority:** Medium

---

### UQ11: Timeline Granularity

**Status:** Pending design validation

**Question:** How detailed should timeline be?

**Options:**
- Show all photos
- Aggregated buckets
- Significant moments only
- User-configurable

**Decision Needed:** Phase 2
**Priority:** Medium

---

## Questions Requiring Stakeholder Input

### UQ12: Mobile Support Level

**Status:** Needs stakeholder alignment

**Question:** What level of mobile support is expected?

**Input Needed From:** Product Manager, UX Designer

**Options:**
- Desktop only
- Basic mobile support
- Full mobile parity

**Decision Needed:** Phase 0
**Priority:** Medium

---

### UQ13: Accessibility Investment

**Status:** Needs stakeholder alignment

**Question:** What level of accessibility investment is appropriate?

**Input Needed From:** Product Manager, Accessibility Specialist

**Options:**
- Basic (keyboard only)
- Standard (WCAG AA)
- Full (screen reader + keyboard + high contrast)

**Decision Needed:** Phase 4
**Priority:** Medium

---

### UQ14: Performance Targets

**Status:** Needs stakeholder alignment

**Question:** Are the performance targets (2s load, 30fps playback) acceptable?

**Input Needed From:** Product Manager, Engineering Lead

**Current Targets:**
- First paint: < 1 second
- Interactive: < 3 seconds
- Playback: 30fps minimum

**Decision Needed:** Phase 0
**Priority:** High

---

## Questions Blocked on External Dependencies

### UQ15: Operation EXIF Coordination

**Status:** Blocked on Operation EXIF timeline

**Question:** Will Operation EXIF changes affect playback implementation?

**Dependency:** Operation EXIF project

**Coordination Needed:**
- Timeline sync
- API change notifications
- Testing coordination

**Decision Needed:** Phase 0
**Priority:** Medium

---

### UQ16: Backend Capacity

**Status:** Blocked on backend team

**Question:** Can backend support cursor pagination and timeline summary endpoint?

**Dependency:** Backend team availability

**Information Needed:**
- Backend capacity
- Timeline for API changes
- Testing support

**Decision Needed:** Phase 1
**Priority:** High

---

### UQ17: Frontend Framework Roadmap

**Status:** Blocked on frontend lead

**Question:** Any plans for React Server Components or framework changes?

**Dependency:** Frontend technical roadmap

**Information Needed:**
- React 19 adoption plans
- Server Components timeline
- State management evolution

**Decision Needed:** Phase 0
**Priority:** Low (verified not planned currently)

---

## Questions with Multiple Valid Options

### UQ18: Frame Step Definition

**Status:** Multiple valid approaches

**Question:** What does "step one frame" mean?

**Rational Options:**
| Option | Pros | Cons |
|--------|------|------|
| 1 photo | Predictable, simple | May skip content |
| 1 second | Time-accurate | Skips photos |
| 1 cluster | Smart grouping | Complex to implement |
| 1 event | AI-powered | Not MVP-ready |

**Current Recommendation:** 1 photo (most straightforward)

**Decision Needed:** Phase 5
**Priority:** Medium

---

### UQ19: Gap Handling

**Status:** Multiple valid approaches

**Question:** How to handle gaps in timeline?

**Rational Options:**
| Option | Pros | Cons |
|--------|------|------|
| Skip | Video-like behavior | May be jarring |
| Pause | User control | May confuse |
| Placeholder | Visual continuity | More UI complexity |
| Compress | Time-accurate | Complex to implement |

**Current Recommendation:** Skip gaps (video-like behavior)

**Decision Needed:** Phase 5
**Priority:** Medium

---

### UQ20: GPS Photo Handling

**Status:** Multiple valid approaches

**Question:** How to handle photos without GPS?

**Rational Options:**
| Option | Pros | Cons |
|--------|------|------|
| Hide map | Clean map | Loses context |
| Keep position | Smooth playback | Map stale |
| Show markers | See context | Cluttered |
| Nearest GPS | Smooth transition | May be misleading |

**Current Recommendation:** Keep last map position (smoothest)

**Decision Needed:** Phase 5
**Priority:** Medium

---

## Questions Needing More Information

### UQ21: User Collection Size Distribution

**Status:** Needs data

**Question:** What percentage of users have 100k+ photos?

**Information Needed:**
- Database query for collection sizes
- Distribution across percentiles

**Current Assumption:** 10% have 100k+

**Verification Needed:** Analytics query
**Priority:** Medium

---

### UQ22: Timestamp Data Quality

**Status:** Needs data

**Question:** What percentage of photos have missing/bad timestamps?

**Information Needed:**
- Database query for NULL timestamps
- Count of future dates
- Count of pre-1990 dates

**Current Assumption:** Generally reliable, outliers exist

**Verification Needed:** Data quality audit
**Priority:** Medium

---

### UQ23: GPS Coverage

**Status:** Needs data

**Question:** What percentage of photos have GPS data?

**Information Needed:**
- Database query for GPS coordinates
- Trend over time

**Current Assumption:** ~40% have GPS (from F9)

**Verification Needed:** Current stats query
**Priority:** Low (already have data)

---

## Questions Marked as "Out of Scope"

### UQ24: Audio Soundtrack

**Status:** Out of Scope

**Question:** Should playback include background music?

**Decision:** Not planned for MVP
**Priority:** N/A

---

### UQ25: AI Captions

**Status:** Out of Scope

**Question:** Should AI generate captions during playback?

**Decision:** Not planned for MVP
**Priority:** N/A

---

### UQ26: Annotations

**Status:** Out of Scope

**Question:** Should users be able to annotate during playback?

**Decision:** Not planned for MVP
**Priority:** N/A

---

### UQ27: Comparison Mode

**Status:** Out of Scope

**Question:** Should playback support side-by-side comparison?

**Decision:** Not planned for MVP
**Priority:** N/A

---

## Questions Summary Table

| ID | Question | Status | Priority | Blocked By | Decision Needed |
|----|----------|--------|----------|------------|-----------------|
| UQ1 | Default speed | Pending research | High | VT1 | Phase 4 |
| UQ2 | Mode persistence | Pending decision | Medium | - | Phase 4 |
| UQ3 | Filter presets | Future | Low | - | Phase 9 |
| UQ4 | Video export | Future | Low | - | Post-MVP |
| UQ5 | Collaboration | Future | Low | - | Post-MVP |
| UQ6 | AI integration | Pending P16 | Low | P16 Phase 3 | TBD |
| UQ7 | Preloading | Pending VT7 | Medium | VT7 | Phase 5 |
| UQ8 | Clustering threshold | Pending VT2 | High | VT2 | Phase 1 |
| UQ9 | Pagination | Pending VT10 | High | VT10 | Phase 1 |
| UQ10 | Zoom levels | Pending design | Medium | - | Phase 2 |
| UQ11 | Timeline granularity | Pending design | Medium | - | Phase 2 |
| UQ12 | Mobile level | Stakeholder | Medium | - | Phase 0 |
| UQ13 | Accessibility | Stakeholder | Medium | - | Phase 4 |
| UQ14 | Performance targets | Stakeholder | High | - | Phase 0 |
| UQ15 | EXIF coordination | External | Medium | OP-EXIF | Phase 0 |
| UQ16 | Backend capacity | External | High | Backend | Phase 1 |
| UQ17 | RSC roadmap | External | Low | Frontend | Phase 0 |
| UQ18 | Frame step | Multiple | Medium | - | Phase 5 |
| UQ19 | Gap handling | Multiple | Medium | - | Phase 5 |
| UQ20 | GPS handling | Multiple | Medium | - | Phase 5 |
| UQ21 | Collection sizes | Needs data | Medium | Analytics | Phase 0 |
| UQ22 | Timestamp quality | Needs data | Medium | Audit | Phase 0 |
| UQ23 | GPS coverage | Needs data | Low | Stats | Phase 0 |

**Total Open Questions:** 23

---

## Resolution Tracking

### Questions Resolved This Session

None yet (initial analysis)

---

### Questions Resolved by Phase

| Phase | Questions | Resolution Method |
|-------|-----------|-------------------|
| Phase 0 | UQ14, UQ15, UQ17, UQ21, UQ22, UQ23 | Stakeholder + Data |
| Phase 1 | UQ8, UQ9, UQ16 | Validation + External |
| Phase 2 | UQ10, UQ11 | Design + Validation |
| Phase 4 | UQ1, UQ2, UQ12, UQ13 | Research + Stakeholder |
| Phase 5 | UQ7, UQ18, UQ19, UQ20 | Validation + Decision |

---

## Help Wanted

| Question | Input Needed |
|----------|-------------|
| UQ1 | User research study |
| UQ12 | Product strategy |
| UQ13 | Accessibility expertise |
| UQ14 | Performance review |
| UQ15 | Operation EXIF timeline |
| UQ16 | Backend capacity |
| UQ21 | Analytics data |
| UQ22 | Data quality report |
