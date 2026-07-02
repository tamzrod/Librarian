# TRACE: Temporal Investigation Workspace

## Design Specification v2.0

> **Purpose**: Transform TRACE from a map with thumbnails into a time-aware investigation workspace where geography and chronology are synchronized.

---

## Core Principle

TRACE investigates:

```
WHERE + WHEN
```

| Element | Represents |
|---------|------------|
| Map | SPACE |
| Timeline | TIME |
| Playback Cursor | CURRENT MOMENT OF INVESTIGATION |

Every visualization reacts to the playhead position.

---

## Success Criteria

A user can answer without leaving TRACE:

- Where was the device?
- When was it there?
- Where did it go next?
- What happened before and after?
- Which evidence belongs together?
- Where did the subject spend the most time?

---

## Investigation Modes

| Mode | Status | Purpose |
|------|--------|---------|
| **Map Mode** | Active | Geographic exploration |
| **Timeline Mode** | Active | Chronological exploration |
| **Grid Mode** | Active | Bulk evidence review |
| **Replay Mode** | Active | Temporal reconstruction / movement replay |
| **Heatmap Mode** | Future | Location density visualization |
| **Route Mode** | Future | Movement analysis |
| **Cluster Mode** | Future | Geographic grouping |

### Why "Replay Mode" Instead of "Story Mode"?

"Story Mode" feels consumer-photo-app oriented. TRACE is an investigation tool.

"Replay" immediately communicates:
- Chronological playback
- Movement reconstruction
- Event sequence analysis

---

## Layout Structure

```
+──────────────────────────────────────────────────────────────+
│ Trace Mode Tabs [Map] [Timeline] [Grid] [Replay] [🌡️Soon] [↗Soon] │
+──────────────────────────────────────────────────────────────+
│                                                              │
│ +──────────────────+────────────────────────────────────+   │
│ │ Filter Palette   │                                    │   │
│ │                  │                                    │   │
│ │ Devices          │                                    │   │
│ │ Years            │                                    │   │
│ │ Unknown Device   │           MAP AREA                 │   │
│ │ Time Range       │                                    │   │
│ │ Playback         │                                    │   │
│ │                  │                                    │   │
│ │ ──────────────── │                                    │   │
│ │                  │                                    │   │
│ │ INVESTIGATION    │                                    │   │
│ │ ANCHORS          │                                    │   │
│ │ [anchor items]   │                                    │   │
│ │                  │                                    │   │
│ │ ──────────────── │                                    │   │
│ │                  │                                    │   │
│ │ STAY POINTS      │                                    │   │
│ │ [future]         │                                    │   │
│ │                  │                                    │   │
│ +──────────────────+────────────────────────────────────+   │
│                                                              │
+──────────────────────────────────────────────────────────────+
│  <<  ▶  >>   2025-06-15 | 14:32:18   ═══════════●═══════════ │
+──────────────────────────────────────────────────────────────+
│ ◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼ │
│ [img][img][img][img][img][img][img][img][img][img][img][img] │
│ ◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼ │
└──────────────────────────────────────────────────────────────┘
```

---

## Filter Palette

### 1. Device Filter

```
☑ HONOR BRP-NX1          (847 photos)
☑ XIAOMI 2109119DG       (523 photos)
☐ Unknown Device          (156 photos)
```

**Unknown Device** includes:
- Missing EXIF data
- Screenshots
- Downloaded images
- Social media images

### 2. Time Range Filter

**Presets:**
- All Time
- Last 24 Hours
- Last 7 Days
- Last 30 Days
- Last 90 Days
- Custom (YYYY-MM-DD HH:mm → YYYY-MM-DD HH:mm)

### 3. Playback Controls

```
⏮ Previous    ▶ Play    ⏸ Pause    ⏭ Next

Speed: [0.5x] [1x] [2x] [5x] [10x]
```

---

## Investigation Anchors

### Concept

Allow investigators to create timeline anchors—user-defined markers that help build narratives from evidence.

### Examples

```
08:15 — Leave Home
09:00 — Arrived Office
12:10 — Lunch Meeting
18:30 — Returned Home
```

### Visual Treatment

Anchors appear:
- On the timeline (film strip)
- On the map (as markers)
- During playback mode

### Implementation Notes

- User creates anchors by clicking the `+` button
- Anchors can be labeled with custom text
- Anchors persist in session (not persisted to backend)
- Anchors can be deleted

### Future Enhancement

Anchor templates for common events:
- "Arrived at [location]"
- "Departed from [location]"
- "Meeting started"
- "Photo captured"

---

## Stay Points (Future Feature)

### Concept

Automatic detection of location dwell time—where the subject spent significant time versus passing through.

### Examples

**Stayed Location:**
```
┌─────────────────────────┐
│ 🏠 Home                 │
│ Duration: 8h 13m        │
│ Photos: 142             │
└─────────────────────────┘
```

**Extended Stay:**
```
┌─────────────────────────┐
│ 🏢 Office               │
│ Duration: 9h 44m        │
│ Photos: 89              │
└─────────────────────────┘
```

**Brief Stop:**
```
┌─────────────────────────┐
│ ⛽ Fuel Station         │
│ Duration: 5m            │
│ Photos: 1               │
└─────────────────────────┘
```

**Passing Through:**
```
┌─────────────────────────┐
│ 🚗 Transit              │
│ Duration: 3m            │
│ Photos: 1               │
└─────────────────────────┘
```

### Detection Criteria

| Type | Duration | Photos |
|------|----------|--------|
| Home | > 6 hours | > 50 |
| Work | > 4 hours | > 20 |
| Brief Stop | 5-30 min | 1-5 |
| Passing Through | < 5 min | 1 |

---

## Film Strip (Temporal Playback Rail)

### Concept

The bottom film strip is **not merely a list of thumbnails**. It behaves as a **temporal playback rail**.

### Rules

| Position | Meaning |
|----------|---------|
| Left | Oldest |
| Right | Newest |
| Current | Always visible, automatically centered |

### Visual States

```
PAST     │ CURRENT │ FUTURE
─────────┼─────────┼────────
dimmed   │highlight│ normal
         │centered │
         │scaled   │
```

### Playback Behavior

When playback runs:

```
playhead moves
        ↓
timeline scrolls (auto-centering)
        ↓
active image changes
        ↓
map centers (if Auto Follow enabled)
        ↓
marker highlighted
        ↓
popup updated
        ↓
photo detail panel updates
```

### Film Strip Aesthetic

- Dark film strip background
- Perforation holes (top and bottom)
- Timestamp labels on hover
- Glow effect on current frame
- Smooth scroll animation

---

## Map Behavior

### Zoom Levels

#### Zoomed Out (Low Zoom)
**Display:** Cluster counts only

```
┌───┐
│125│
└───┘   ┌───┐
        │84 │
        └───┘   ┌───┐
                │33 │
                └───┘
```

#### Medium Zoom
**Display:** Smaller clusters

```
┌───┐
│15 │
└───┘   ┌───┐
        │12 │
        └───┘
```

#### High Zoom
**Display:** Individual thumbnail markers

```
📷  📷  📷
```

#### Maximum Zoom
**Display:** Thumbnail callouts anchored to exact GPS

```
┌──────────────┐
│ [thumbnail]  │
│ 14:32:18    │
│ HONOR BRP   │
└──────┬───────┘
       ● GPS Point
```

### Cluster Display

Clusters show:
- Image count
- Representative image
- Dominant device
- Dominant time period

```
┌─────────────┐
│ [thumb]     │
│ 35 photos   │
│ 2025-06     │
│ HONOR BRP   │
└─────────────┘
```

---

## Route Intelligence

### Visualization

Replay mode displays:
- Route lines connecting photos chronologically
- Travel direction indicators
- Movement order (numbered markers)

### Color Gradient

```
Green ───── Yellow ───── Red
(old)       (mid)      (recent)
```

### Travel Direction

Optional arrow indicators show direction of movement:

```
[1] ──→ [2] ──→ [3] ──→ [4]
```

### Future Enhancement

**Animated Travel Playback:**
- Moving dot along route line
- Trail effect showing path taken
- Speed proportional to travel time

---

## Design Language

### Aesthetic
**Tactical/Forensic Interface** — Dark, immersive, mission control inspired.

### Color Palette

```css
--bg-primary:      #0a0c10    /* Deep blue-black */
--bg-secondary:    #12151c    /* Panel backgrounds */
--bg-tertiary:    #1a1e28    /* Card backgrounds */
--bg-elevated:    #232936    /* Hover states */

--accent-cyan:     #00d4ff   /* Primary accent */
--accent-magenta:  #ff3d8e   /* Secondary accent */
--accent-amber:    #ffb020   /* Highlights (anchors) */

--route-old:       #22c55e   /* Green - old photos */
--route-mid:       #eab308   /* Yellow - middle */
--route-recent:    #ef4444   /* Red - recent photos */

--text-primary:    #f1f5f9
--text-secondary:  #94a3b8
--text-tertiary:   #64748b
--text-muted:      #475569
```

### Typography

| Element | Font | Usage |
|---------|------|-------|
| Technical data | JetBrains Mono | Timestamps, coordinates, counts |
| UI text | Outfit | Labels, buttons, navigation |
| Headers | Outfit | Section titles, mode names |

### Components

- **Playhead**: Glowing cyan indicator with time display
- **Film frames**: 72×72px thumbnails with perforation styling
- **Markers**: Circular with thumbnail images or count numbers
- **Anchors**: Amber-bordered items with timeline markers
- **Popups**: Card-style with thumbnail, timestamp, device, coordinates

---

## Implementation Phases

### Phase 1
- [x] Unknown Device filter
- [x] Time range filter
- [x] Chronological film strip
- [x] Investigation Anchors

### Phase 2
- [x] Playback controls
- [x] Playhead
- [x] Active image highlighting

### Phase 3
- [x] Route lines
- [x] Auto follow mode
- [x] Map synchronization
- [ ] Route direction indicators

### Phase 4
- [ ] Thumbnail markers at max zoom
- [ ] Dynamic clustering
- [x] Replay mode
- [ ] Animated travel playback

### Phase 5
- [ ] Heatmaps
- [ ] Stay point detection
- [ ] Movement analytics

---

## API Requirements (For Backend)

```typescript
// Get photos with GPS data
GET /api/photos?start_date=&end_date=&devices=[]

// Response
{
  photos: [
    {
      id: string,
      timestamp: ISO8601,
      lat: number,
      lng: number,
      device: string,
      thumbnail_url: string
    }
  ],
  total: number,
  clusters: [
    {
      center: [lat, lng],
      count: number,
      dominant_device: string,
      date_range: [start, end]
    }
  ]
}

// Stay point analysis (future)
GET /api/photos/stay-points?min_duration=30min

// Response
{
  stay_points: [
    {
      location: [lat, lng],
      duration_minutes: number,
      photo_count: number,
      type: 'home' | 'work' | 'transit' | 'brief'
    }
  ]
}
```

---

## Notes

- This is a **UI/UX design and documentation** update
- No backend implementation
- No API implementation
- No worker implementation
- No database changes
- Focus: UI architecture, workflow, investigator experience
