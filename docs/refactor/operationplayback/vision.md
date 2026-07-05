# Vision — Operation Playback

## Vision Statement

> **Operation Playback** transforms the Trace workspace from a static exploration interface into an immersive, video-like experience where users can play through their photo history as a synchronized, cinematic journey through time and space.

---

## Core Concept

Operation Playback treats your photo collection not as a database to query, but as a **journey to experience**. Users become investigators, journalists, or travelers—watching their own history unfold frame by frame.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   "What if browsing photos was like watching a travel documentary?"         │
│                                                                             │
│   "What if I could press PLAY and watch my life unfold?"                    │
│                                                                             │
│   "What if the map moved WITH the filmstrip AND the timeline?"              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Playback Metaphor

### Before: Query-Based Exploration

Users currently interact with Trace through:
- Point-and-click navigation
- Filter selection
- Tab switching between Map/Timeline/Grid
- Manual scrolling through filmstrip
- Separate mental models for each view

### After: Playback-Based Experience

Users interact with Operation Playback through:
- **Play** — Watch the story unfold automatically
- **Scrub** — Drag through time like a video editor
- **Reverse** — Travel backwards through history
- **Hover** — Preview any moment in time instantly
- **Sync** — All views move together as one unified experience

---

## Design Philosophy

### 1. Cinematic Time Travel

The workspace behaves like a video player:
- One unified timeline as the x-axis
- Playhead shows current position in time
- All visualizations (map, filmstrip, markers) synchronized to playhead
- Smooth transitions between frames

### 2. Spatial-Temporal Unity

Time and space are not separate dimensions—they are two views of the same moment:

```
                    PLAYHEAD POSITION: 2026-01-08 14:32
                    
    ┌──────────────────────────────────────────────────────────────┐
    │                         MAP                                   │
    │                                                                │
    │                    📍 ← You are here                          │
    │                   (selected photo marker)                      │
    │                                                                │
    ├──────────────────────────────────────────────────────────────┤
    │  FILMSTRIP                    CURRENT FRAME                   │
    │  ┌────┐ ┌────┐ ┌────┐ ┌────────────────────────────────────┐ │
    │  │ 1  │ │ 2  │ │▓▓▓│ │         CURRENT PHOTO               │ │
    │  └────┘ └────┘ └────┘ └────────────────────────────────────┘ │
    ├──────────────────────────────────────────────────────────────┤
    │  TIMELINE X-AXIS                                              │
    │  ◄──────────────●──────────────────────────────────►         │
    │  Jan 1          ↑                                    Dec 31    │
    │            Playhead                                            │
    └──────────────────────────────────────────────────────────────┘
```

### 3. Progressive Disclosure

Not everyone wants the full experience immediately:

- **Beginner Mode**: Single Play button, basic controls
- **Standard Mode**: Full playback controls, filmstrip
- **Advanced Mode**: Speed controls, reverse, frame-by-frame

### 4. Performance by Default

Large collections (100k+ images) must work smoothly:
- Virtual scrolling for filmstrip
- Clustered markers on map
- Lazy loading of thumbnails
- Efficient data fetching with pagination

---

## Core Interactions

### Playback Controls

| Control | Behavior | Keyboard |
|---------|----------|----------|
| Play | Begin forward playback from playhead | `Space` |
| Pause | Freeze playback at current position | `Space` |
| Stop | Return playhead to start | `S` |
| Reverse | Play backwards through time | `R` |
| Speed | Playback speed (0.5x to 32x) | `+`/`-` |
| Step | Move one frame at a time | `←`/`→` |
| Jump | Jump to specific time/date | `J` |

### Hover Previews

| Element | Hover Behavior |
|---------|----------------|
| Filmstrip Frame | Show enlarged thumbnail preview |
| Map Marker | Show thumbnail + metadata tooltip |
| Timeline Segment | Show count and date range |
| Filter Pill | Show affected item count |

### Synchronization

When playhead moves (via any method):
1. Map pans/zooms to center on current photo's location
2. Filmstrip scrolls to show current frame
3. Event details update in sidebar
4. Timeline marker updates position

---

## Visual Design Direction

### Timeline as Primary Navigation

The timeline is no longer a hidden feature—it's the **primary navigation element**:

```
┌──────────────────────────────────────────────────────────────────────┐
│  ▶️  ⏸️  ⏹️  🔄  │ Speed: [1x ▼]  │ 00:15:32 ────●────── 02:45:00  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  2026-01                        2026-06                        2026-12 │
│     │                              │                              │     │
│     ●──────────────────────────────●──────────────────────────────●   │
│     ↑                              ↑                              ↑   │
│   Jan 8                         Jul 5                          Dec 31 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Filmstrip Becomes Primary View

The filmstrip expands and becomes the hero element:

```
┌──────────────────────────────────────────────────────────────────────┐
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ │
│  │     │ │     │ │▓▓▓▓▓│ │     │ │     │ │     │ │     │ │     │ │
│  │  1  │ │  2  │ │  3  │ │  4  │ │  5  │ │  6  │ │  7  │ │  8  │ │
│  │     │ │     │ │SELECT│ │     │ │     │ │     │ │     │ │     │ │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ │
│                                                                      │
│  ◄══════════════════ 12,847 photos ════════════════════════════►   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Map Follows Playhead

The map automatically updates to show the current photo's location:

```
┌──────────────────────────────────────────────────────────────────────┐
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                                                                │  │
│  │                         🗺️ MAP                                 │  │
│  │                                                                │  │
│  │                    📍 ← Playhead photo                         │  │
│  │                   ╱                                            │  │
│  │                  ╱                                             │  │
│  │                 ╱  📍 ← Previous route                         │  │
│  │                ╱                                               │  │
│  │           📍 ─┴─ 📍 ← Clustered photos                        │  │
│  │                                                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  [🗺️ Map View]  [🧭 Route View]  [📊 Cluster View]                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Relationship to Existing Trace

Operation Playback builds upon the existing Trace architecture:

| Current Trace | Operation Playback Evolution |
|---------------|------------------------------|
| FilterPalette | FilterPalette (enhanced) |
| MapCanvas | MapCanvas (follows playhead) |
| FilmStrip | FilmStrip (expanded, primary view) |
| EventStream | **Removed** → Replaced by Timeline X-axis |
| FilterPalette → Years | **Removed** → Continuous timeline replaces discrete years |
| View tabs (Map/Timeline/Grid) | **Simplified** → Unified playback view |

---

## Success Criteria

Operation Playback is successful when:

1. **Engagement** — Users spend 3x longer in Trace (active playback vs. passive browsing)
2. **Discovery** — Users discover 2x more photos through playback than through filtering
3. **Satisfaction** — "Like watching a documentary of my life" feedback
4. **Performance** — 100k photo collections play smoothly at 60fps
5. **Accessibility** — Full functionality available via keyboard for accessibility

---

## Future Extensions (Out of Scope for Initial Release)

- Animated route visualization on map
- Video export of playback session
- Collaborative playback sessions
- AI-generated captions during playback
- Music/soundtrack integration

---

*Operation Playback: Watch your history unfold.*
