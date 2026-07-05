# Migration Strategy — Operation Playback

## Overview

This document describes the strategy for migrating from the current Trace implementation to the Operation Playback workspace.

---

## Migration Principles

1. **Backward Compatibility First** — Existing URLs, filters, and functionality must continue to work
2. **Incremental Rollout** — Deploy features gradually, not all at once
3. **Feature Flags** — Use feature flags to control what users see
4. **Graceful Degradation** — Older browsers/devices get reduced functionality
5. **Rollback Capability** — Every change must be reversible

---

## Migration Phases

### Phase M0: Preparation (Before Code Changes)

**Goal:** Set up infrastructure for safe migration.

**Tasks:**
- [ ] Implement feature flag system
- [ ] Set up analytics for Operation Playback metrics
- [ ] Create migration test suite
- [ ] Document rollback procedures
- [ ] Train support team on new functionality

### Phase M1: Add Timeline X-axis

**Goal:** Add timeline without removing existing functionality.

**Changes:**
- Add new `TimelineAxis` component
- Timeline appears above EventStream (not replacing)
- Existing view modes continue to work
- Feature flag: `enable_timeline_axis`

**Migration Path:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ BEFORE                         AFTER                                │
│                                                                      │
│ ┌───────────────────┐          ┌─────────────────────────────────┐ │
│ │ Filter Palette   │          │ Filter Palette                  │ │
│ └───────────────────┘          └─────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Map / Timeline / Grid                                           │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Film Strip                                                     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Event Stream                                                   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│                              ↓ becomes ↓                              │
│                                                                      │
│ ┌───────────────────┐          ┌─────────────────────────────────┐ │
│ │ Filter Palette   │          │ Filter Palette                  │ │
│ └───────────────────┘          └─────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Map / Timeline / Grid                                           │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Film Strip                                                     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ ═══════════ TIMELINE X-AXIS ═══════════                         │ │
│ │  ◄──────────────●──────────────────────────────────►           │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Event Stream (Still functional, not primary)                     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Phase M2: Add Playback Controls

**Goal:** Introduce playback controls while keeping all existing functionality.

**Changes:**
- Add `PlaybackControls` component
- Integrate with timeline axis
- Add keyboard shortcuts
- Feature flag: `enable_playback_controls`

**Migration Path:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ ▶️ ⏸️ ⏹️  │ Speed: [1x ▼] │ 00:15:32 ────●────── 02:45:00   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ ═══════════ TIMELINE X-AXIS ═══════════                         │ │
│ │  ◄──────────────●──────────────────────────────────►           │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Map / Timeline / Grid                                           │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Film Strip                                                     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Event Stream (Secondary)                                        │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Phase M3: Implement Synchronization

**Goal:** Connect map, filmstrip, and timeline for synchronized playback.

**Changes:**
- Add sync state management to TraceView
- Map follows playhead during playback
- Filmstrip scrolls to current frame
- Feature flag: `enable_playback_sync`

**Migration Path:**
```
User clicks filmstrip frame:
┌─────────────────────────────────────────────────────────────────────┐
│  BEFORE:                       AFTER:                                │
│                                                                      │
│  Filmstrip click ──▶ Selected document ID only                      │
│                                                                      │
│                    Filmstrip click ──┬──▶ Map centers on location   │
│                                         └──▶ Timeline updates       │
│                                         └──▶ EventStream updates    │
└─────────────────────────────────────────────────────────────────────┘
```

### Phase M4: Add Hover Previews

**Goal:** Enhance user experience with thumbnail previews.

**Changes:**
- Thumbnail hover preview in FilmStrip
- Marker hover preview in MapCanvas
- Feature flag: `enable_hover_previews`

### Phase M5: Remove Years Filter

**Goal:** Replace discrete years filter with continuous timeline.

**Changes:**
- Remove years filter group from FilterPalette
- Update FilterState interface
- Update API to ignore `years` parameter
- Feature flag: `disable_years_filter`

**Migration Path:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ BEFORE                         AFTER                                │
│                                                                      │
│ Filter Palette:                 Filter Palette:                      │
│ ┌─────────────────┐             ┌─────────────────────────────────┐ │
│ │ ▼ DEVICES      │             │ ▼ DEVICES                      │ │
│ │ ▼ SOURCES      │             │ ▼ SOURCES                      │ │
│ │ ▼ YEARS        │             │ [YEARS REMOVED]                 │ │
│ │   ☑ 2026 (247) │             │ ▼ TIME RANGE (enhanced)         │ │
│ │   ☑ 2025 (892) │             │   Timeline picker               │ │
│ │   ☐ 2024 (0)   │             └─────────────────────────────────┘ │
│ └─────────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

**URL Migration:**
- Old URL: `/trace?years=2025,2026`
- New URL: `/trace?startDate=2025-01-01&endDate=2026-12-31`
- Redirect rule: Parse `years` param, convert to date range

### Phase M6: Expand Filmstrip

**Goal:** Make filmstrip larger and more prominent.

**Changes:**
- Increase filmstrip height
- Larger thumbnail sizes
- Optional fullscreen mode
- Feature flag: `expanded_filmstrip`

### Phase M7: Remove Event Stream

**Goal:** Remove EventStream component entirely, replace with timeline-based interaction.

**Changes:**
- Remove EventStream component
- Timeline becomes the primary event list
- Feature flag: `remove_event_stream`

**Migration Path:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ BEFORE                         AFTER                                │
│                                                                      │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Film Strip                                                     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ ═══════════ TIMELINE X-AXIS ═══════════                         │ │
│ │  Click any point to see events at that time                     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Event Stream         ──▶  REMOVED                               │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Feature Flag Strategy

### Implementation

Use a simple feature flag system:

```typescript
// src/config/featureFlags.ts
export const FEATURE_FLAGS = {
  enable_timeline_axis: true,       // Phase M1
  enable_playback_controls: true,   // Phase M2
  enable_playback_sync: true,       // Phase M3
  enable_hover_previews: true,      // Phase M4
  disable_years_filter: false,      // Phase M5
  expanded_filmstrip: false,        // Phase M6
  remove_event_stream: false,       // Phase M7
} as const;

export type FeatureFlag = keyof typeof FEATURE_FLAGS;

export function isEnabled(flag: FeatureFlag): boolean {
  // Check localStorage override first
  const stored = localStorage.getItem(`feature_${flag}`);
  if (stored !== null) return stored === 'true';
  // Fall back to config
  return FEATURE_FLAGS[flag];
}
```

### URL Override

Users can enable/disable features via URL:

```
/trace?feature.enable_timeline_axis=false
/trace?feature.expanded_filmstrip=true
```

### Admin Override

Support team can enable any flag for specific users via admin panel.

---

## URL and State Migration

### Current URL Patterns

```
/trace                          # Main trace view
/trace?view=map                # Map view
/trace?view=timeline           # Timeline view (placeholder)
/trace?view=grid               # Grid view (placeholder)
/trace?cameras=HONOR,Xiaomi    # Device filter
/trace?years=2025,2026         # Years filter (to be deprecated)
/trace?startDate=...&endDate=...  # Date range filter
```

### Operation Playback URL Patterns

```
/trace                                   # Default: Operation Playback enabled
/trace?playback=disabled                 # Disable playback, legacy mode
/trace?playback=play&speed=2            # Start in playing mode
/trace?timestamp=2026-01-08T14:32:00    # Jump to specific time
/trace?startDate=...&endDate=...        # Date range filter
```

### Migration Rules

| Old URL | New URL | Behavior |
|---------|---------|----------|
| `/trace?view=map` | `/trace` | Map still available, timeline added |
| `/trace?view=timeline` | `/trace` | Timeline now default |
| `/trace?view=grid` | `/trace` | Grid available via view toggle |
| `/trace?years=2025` | `/trace?startDate=2025-01-01&endDate=2025-12-31` | Auto-convert |
| `/trace?cameras=HONOR` | `/trace?cameras=HONOR` | No change |

---

## Backward Compatibility Checklist

### API Compatibility

- [ ] `years` parameter still accepted, logged as deprecated
- [ ] `view` parameter still accepted, logged as deprecated
- [ ] `events` response format unchanged
- [ ] `markers` response format unchanged
- [ ] Pagination additions are backward compatible

### Component Compatibility

- [ ] All components render without Operation Playback flags
- [ ] EventStream still renders when `remove_event_stream=false`
- [ ] Years filter still renders when `disable_years_filter=false`
- [ ] Filter state is compatible with both old and new models

### Browser Compatibility

- [ ] IE11: Disabled Operation Playback features, basic Trace works
- [ ] Safari 14: Full Operation Playback support
- [ ] Mobile Safari: Reduced functionality (no keyboard shortcuts)
- [ ] Chrome: Full Operation Playback support

---

## Rollback Procedures

### Quick Rollback (Feature Flag)

```typescript
// Disable problematic feature
localStorage.setItem('feature_enable_playback_controls', 'false');
// Or via URL
/trace?feature.enable_playback_controls=false
```

### Full Rollback (Code)

```bash
# Revert to previous commit
git revert HEAD
# Or
git checkout <previous-tag>
```

### Data Rollback

No data migrations are required for Operation Playback. All changes are:
- Frontend-only
- Reversible without database changes
- Backward compatible with existing data

---

## Testing Strategy

### Migration Testing Matrix

| From State | To State | Test Focus |
|-----------|----------|------------|
| Legacy Trace | Phase M1 | Timeline appears correctly |
| Phase M1 | Phase M2 | Playback controls work |
| Phase M2 | Phase M3 | Synchronization functions |
| Phase M3 | Phase M4 | Hover previews work |
| Phase M4 | Phase M5 | Years filter removal |
| Phase M5 | Phase M6 | Filmstrip expansion |
| Phase M6 | Phase M7 | EventStream removal |

### Regression Testing

For each phase, verify:
- [ ] Existing URLs continue to work
- [ ] Existing filters continue to work
- [ ] Map interactions unchanged
- [ ] Filmstrip interactions unchanged
- [ ] EventStream (if still present) unchanged
- [ ] No console errors
- [ ] No layout breaks

### Load Testing

- [ ] 1,000 items: Full functionality
- [ ] 10,000 items: Smooth playback
- [ ] 100,000 items: Virtualization working
- [ ] 500,000 items: Graceful degradation

---

## User Communication

### Announcement Template

```
Subject: New Feature: Operation Playback in Trace

We're excited to introduce Operation Playback, a new way to explore your photo collection.

What's new:
- 📅 Timeline X-axis for easy navigation through time
- ▶️ Play/pause controls to watch your photos unfold
- 🔄 Synchronized views: map, filmstrip, and timeline move together
- ✨ Hover previews on photos and map markers

How to use:
1. Open Trace as usual
2. Look for the new timeline at the bottom
3. Press the Play button to start playback
4. Use the timeline to jump to any point in time

Feedback: [link to feedback form]
```

### Help Documentation

Create help section:
- Getting Started with Operation Playback
- Keyboard Shortcuts
- Troubleshooting
- FAQ

---

## Go-Live Checklist

### Pre-Launch

- [ ] All feature flags configured correctly
- [ ] Analytics tracking implemented
- [ ] Help documentation published
- [ ] Support team trained
- [ ] Rollback plan tested

### Launch Day

- [ ] Monitor error rates
- [ ] Watch analytics dashboards
- [ ] Enable user feedback channel
- [ ] Have rollback ready to execute

### Post-Launch

- [ ] Gather user feedback
- [ ] Monitor feature adoption
- [ ] Address reported issues
- [ ] Plan next iteration
