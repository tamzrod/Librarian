# UI_LAYOUT.md — Unified Trace Workspace Design

## Overview

This document defines the unified Trace workspace layout, component positioning, and interaction patterns.

## Layout Philosophy

### Design Principles

1. **Information Density** — Maximize visible data without overwhelming
2. **Spatial Organization** — Filters on left, content center, details right
3. **Progressive Disclosure** — Simple by default, expand on demand
4. **Responsive Adaptation** — Adapts to screen size and device
5. **Keyboard-First** — All actions accessible via keyboard shortcuts

### Visual Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│ PRIMARY: Playback Controls (most important interaction)              │
├──────────────┬─────────────────────────────────────┬───────────────┤
│ SECONDARY:   │                                     │ TERTIARY:     │
│ Filter       │  TRACE CANVAS                        │ Details       │
│ Palette      │  (Map + Timeline + Clusters)         │ Panel         │
│              │                                      │               │
│ (280px)      │  (flexible)                          │ (360px)       │
├──────────────┴─────────────────────────────────────┴───────────────┤
│ EVENT STREAM (collapsible, 200px default)                         │
│ Timeline of filtered items                                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Default Layout

### Desktop (> 1200px)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Trace Controls                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ [⏹ Stop] [▶ Play] [⏸ Pause] │ Speed: [1x ▼] │ [🔊 Mute]     │ │
│  └────────────────────────────────────────────────────────────────┘ │
├───────────────┬──────────────────────────────────────────┬─────────┤
│               │                                          │         │
│  FILTERS      │         MAP / TRACE CANVAS               │ DETAILS │
│               │                                          │         │
│  ┌─────────┐  │    ┌────────────────────────────────┐   │ ┌─────┐ │
│  │ ▼ Devices│  │    │                                │   │ │     │ │
│  │ ☑ HONOR │  │    │       🗺️                        │   │ │ 👤  │ │
│  │ ☑ Xiaomi│  │    │                                │   │ │     │ │
│  │ ☐ iPhone│  │    │         ●───●───●               │   │ │  📷 │ │
│  │ ☐ DJI   │  │    │        /                         │   │ │     │ │
│  ├─────────┤  │    │       ●                          │   │ │     │ │
│  │ ▼ Sources│ │    │                                │   │ │     │ │
│  │ ☑ GPS   │  │    │     ●──────●                    │   │ │     │ │
│  │ ☑ OCR   │  │    │                                │   │ │     │ │
│  ├─────────┤  │    │                                │   │ │     │ │
│  │ ▼ Types │  │    └────────────────────────────────┘   │ │     │ │
│  │ ☑ Images│  │                                          │ │     │ │
│  │ ☑ Video │  │    [🗺️ Map] [📅 Timeline] [🧭 Trace]   │ │     │ │
│  │ ☐ Docs  │  │                                          │ │     │ │
│  ├─────────┤  │                                          │ └─────┘ │
│  │ ▼ Collect│ │                                          │         │
│  │ ☑ Camera │ │                                          │         │
│  │ ☑ Evidence│ │                                          │         │
│  └─────────┘  │                                          │         │
│               │                                          │         │
│  [Clear All]  │                                          │         │
│               │                                          │         │
├───────────────┴──────────────────────────────────────────┴─────────┤
│  EVENT STREAM                                          [▲ Collapse] │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 2026-01-08 14:32 │ HONOR BRP-NX1 │ Times Square │    [thumb] │  │
│  │ 2026-01-08 14:45 │ HONOR BRP-NX1 │ Central Park │   [thumb] │  │
│  │ 2026-02-18 09:15 │ Xiaomi 2109119DG │ Office │        [thumb] │  │
│  │ 2026-02-18 12:30 │ Xiaomi 2109119DG │ Home │           [thumb] │  │
│  │ 2026-05-27 18:45 │ HONOR BRP-NX1 │ Beach │           [thumb] │  │
│  └──────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Specifications

#### 1. Trace Controls (Top Bar)

**Height:** 56px  
**Position:** Fixed top  
**Background:** #1a1a1a (dark)  
**Border:** 1px solid #333

```
┌──────────────────────────────────────────────────────────────────────┐
│ ┌──────┐ ┌──────┐ ┌──────┐ │ ┌────────┐ ┌────────┐ │ ┌────────┐   │
│ │ ⏹    │ │ ▶    │ │ ⏸    │ │ │ Speed  │ │ Volume │ │ │ Views  │   │
│ │ Stop │ │ Play │ │ Pause │ │ │  1x ▼  │ │ 🔊 80% │ │ │ Grid▼  │   │
│ └──────┘ └──────┘ └──────┘ │ └────────┘ └────────┘ │ └────────┘   │
│                                                                      │
│ Playback: [━━━━━━━━━━●━━━━━━━━━━━━] 00:15:32 / 02:45:00           │
└──────────────────────────────────────────────────────────────────────┘
```

**Elements:**
| Element | Type | Default | Options |
|---------|------|---------|---------|
| Stop | Icon Button | Enabled | - |
| Play/Pause | Icon Button | Toggle | Play when stopped, Pause when playing |
| Speed | Dropdown | 1x | 0.5x, 1x, 2x, 4x, 8x, 16x |
| Volume | Slider | 80% | 0-100% |
| View Toggle | Dropdown | Map | Map, Timeline, Trace, Grid |
| Time Scrubber | Range | - | Drag to seek |
| Time Display | Text | - | Current / Total |

#### 2. Filter Palette (Left Sidebar)

**Width:** 280px (collapsible to 48px)  
**Background:** #242424  
**Border Right:** 1px solid #333

```
┌────────────────────────────────┐
│ 🔍 Filter Palette    [⌨] [×]  │
├────────────────────────────────┤
│                                │
│ ▼ DEVICES              2/5    │
│ ├─ ☑ HONOR BRP-NX1 (1,247)  │
│ ├─ ☑ Xiaomi 2109119DG (892) │
│ ├─ ☐ iPhone              (0) │
│ ├─ ☐ DJI Drone         (156)│
│ └─ ☐ Canon DSLR          (43)│
│                                │
│ ▼ SOURCES               2/4  │
│ ├─ ☑ GPS EXIF       (2,156) │
│ ├─ ☑ OCR              (312) │
│ ├─ ☐ Manual Tag        (89) │
│ └─ ☐ Semantic         (445)│
│                                │
│ ▼ TYPES                 3/4  │
│ ├─ ☑ Images       (2,890)  │
│ ├─ ☑ Video         (267)   │
│ ├─ ☐ Documents       (45)  │
│ └─ ☑ Audio          (12)   │
│                                │
│ ▼ COLLECTIONS           2/8  │
│ ├─ ☑ Camera Roll (2,156)  │
│ ├─ ☑ Evidence     (312)   │
│ ├─ ☐ Project Alpha   (89) │
│ └─ [+ Show 5 more]         │
│                                │
│ ▼ TIME RANGE                 │
│ [2023] [2024] [☑2025] [2026] │
│                                │
│ ▶ LOCATION (click to expand)  │
│ ▶ TAGS (click to expand)      │
│ ▶ ENTITIES (click to expand)  │
│ ▶ ADVANCED (click to expand)  │
│                                │
├────────────────────────────────┤
│ Showing: 3,214 of 3,891      │
│                                │
│ [Clear All] [Save Preset]    │
└────────────────────────────────┘
```

**Interactions:**
- Click category header → Expand/collapse
- Click checkbox → Toggle filter
- Right-click → Multi-select mode
- Drag category → Reorder
- Double-click header → Collapse all

**Keyboard Shortcuts:**
- `Ctrl+F` — Focus filter search
- `Ctrl+1-9` — Toggle filter preset
- `Ctrl+Shift+C` — Clear all filters
- `Escape` — Close palette

#### 3. Trace Canvas (Center)

**Dimensions:** Flexible (fills remaining space)  
**Background:** Map or Timeline view  
**Controls:** Floating overlay

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│                         🗺️ MAP VIEW                                 │
│                                                                      │
│                  ┌─────────────────────────────────┐                │
│                  │                                 │                │
│                  │         📍                       │                │
│                  │          │                       │                │
│                  │          │ Trace Path             │                │
│                  │          │                       │                │
│                  │     ●────●────●                 │                │
│                  │    /                             │                │
│                  │   ●                              │                │
│                  │                                  │                │
│                  │  ●─────────●                    │                │
│                  │                                  │                │
│                  │     ●                            │                │
│                  │                                  │                │
│                  └─────────────────────────────────┘                │
│                                                                      │
│    [+] [-] [⊙] [🛰️] [🌐]              [⚙] [⛶ Fullscreen]       │
│    Zoom In  Zoom  GPS  Satellite  Layers    Settings  Expand      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**View Modes:**

| Mode | Description | Trigger |
|------|-------------|---------|
| Map | Geographic view with markers and routes | Default |
| Timeline | Chronological horizontal view | Toggle |
| Trace | Unified spatial-temporal canvas | Toggle |
| Grid | Thumbnail grid | Toggle |

**Canvas Controls:**
- `+` / `-` — Zoom in/out
- `⊙` — Center on current position
- `🛰️` — Toggle satellite/street view
- `🌐` — Open layers panel
- `⚙` — Open settings
- `⛶` — Enter fullscreen

#### 4. Details Panel (Right Sidebar)

**Width:** 360px (collapsible)  
**Background:** #1a1a1a  
**Border Left:** 1px solid #333

```
┌────────────────────────────────────────┐
│  📷 IMG_4521.jpg                       │
│  January 8, 2026 2:32 PM              │
├────────────────────────────────────────┤
│                                        │
│  ┌──────────────────────────────────┐  │
│  │                                  │  │
│  │         [Thumbnail]              │  │
│  │                                  │  │
│  │                                  │  │
│  └──────────────────────────────────┘  │
│                                        │
│  ──────────────────────────────────   │
│  📍 Location                          │
│  Times Square, Manhattan              │
│  40.7580° N, 73.9855° W              │
│                                        │
│  📱 Device                           │
│  HONOR BRP-NX1                       │
│  Smartphone                          │
│                                        │
│  🏷️ Tags                             │
│  [important] [nyc] [vacation]        │
│  [+ Add tag]                         │
│                                        │
│  👤 People                           │
│  [John Smith] [Known ✓]             │
│  [Jane Doe] [Known ✓]               │
│                                        │
│  🔗 Related                          │
│  [3 similar] [1 duplicate]          │
│  [Same event: NYC Trip]             │
│                                        │
│  ──────────────────────────────────   │
│                                        │
│  [Edit] [Share] [Download] [Delete] │
│                                        │
└────────────────────────────────────────┘
```

**Sections:**
| Section | Collapsible | Content |
|---------|-------------|---------|
| Preview | No | Thumbnail, full image link |
| Location | Yes | Address, coordinates, map link |
| Device | Yes | Make, model, device info |
| Tags | No | Tag chips, add/remove |
| People | Yes | Detected faces, names |
| Objects | Yes | Detected objects |
| Places | Yes | Recognized places |
| Related | Yes | Linked artifacts |
| Actions | No | Edit, share, download, delete |

#### 5. Event Stream (Bottom)

**Height:** 200px (default), collapsible to 40px  
**Background:** #1e1e1e  
**Border Top:** 1px solid #333

```
┌──────────────────────────────────────────────────────────────────────┐
│  EVENT STREAM                                    [🔍] [📊] [▲]     │
│  (filter)  (stats)  (collapse)                                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 2026-01-08 14:32 │ HONOR BRP-NX1 │ Times Square, NYC │  📷  │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ 2026-01-08 14:45 │ HONOR BRP-NX1 │ Central Park, NYC │  📷  │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ 2026-02-18 09:15 │ Xiaomi 2109119DG │ Office │  📷           │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ 2026-02-18 12:30 │ Xiaomi 2109119DG │ Home │  📷             │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ 2026-05-27 18:45 │ HONOR BRP-NX1 │ Beach │  📷              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ◀ [1] [2] [3] ... [15] [▶] │ Showing 1-50 of 3,214              │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Row Content:**
| Column | Width | Content |
|--------|-------|---------|
| Date/Time | 160px | Formatted timestamp |
| Device | 140px | Device name/icon |
| Location | flex | Reverse geocoded address |
| Thumbnail | 60px | Small preview |
| Actions | 80px | Quick actions menu |

**Features:**
- Virtual scrolling for performance
- Click row → Select item
- Double-click → Open detail view
- Right-click → Context menu
- Drag → Reorder (in custom views)

---

## Fullscreen Mode

Activated by clicking expand button or `F11`.

```
┌──────────────────────────────────────────────────────────────────────┐
│  Trace Controls (auto-hide after 3s)                                │
│  [⏹] [▶] [⏸] │ 1x │ [━━━━━━━━●━━━━━━━━━] │ [✕ Exit Fullscreen] │
└──────────────────────────────────────────────────────────────────────┘
                                                                      │
                         FULLSCREEN MAP / TRACE CANVAS                │
                                                                      │
                         ════════════════════════════                 │
                         ║                         ║                  │
                         ║    ●────●────●          ║                  │
                         ║   /                      ║                  │
                         ║  ●                       ║                  │
                         ║          ●────────●      ║                  │
                         ║                          ║                  │
                         ║       ●                  ║                  │
                         ════════════════════════════                 │
                                                                      │
                         [🗺️] [📅] [🧭] [▤]                          │
                         (view toggles)                               │
                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Behavior:**
- All panels hidden
- Controls auto-hide after 3 seconds of inactivity
- Move mouse to edge → Show controls
- `Escape` or `F11` → Exit fullscreen

---

## Dockable Panel Layout

For power users, all panels can be docked to different positions.

### Dockable Options

```
┌──────────────────────────────────────────────────────────────────────┐
│  [Layout Presets ▼]                                                  │
├──────────────┬───────────────────────────────┬──────────────────────┤
│              │                               │                      │
│  Filter      │      Map / Canvas             │   Details            │
│  Palette     │                               │   Panel              │
│  (dockable)  │                               │   (dockable)         │
│              │                               │                      │
│  • Left      │   • Center (default)          │   • Right (default) │
│  • Right     │   • Full                      │   • Left              │
│  • Bottom    │   • Left+Right                │   • Bottom            │
│  • Float     │                               │   • Float            │
│  • Hidden    │                               │   • Hidden           │
│              │                               │                      │
├──────────────┴───────────────────────────────┴──────────────────────┤
│  Event Stream (dockable)                                            │
│  • Bottom (default)                                                  │
│  • Top                                                                │
│  • Left (vertical)                                                   │
│  • Right (vertical)                                                  │
│  • Hidden                                                             │
└──────────────────────────────────────────────────────────────────────┘
```

### Layout Presets

```
┌──────────────────────────────────────────────────────────────────────┐
│  Layout: [Investigation ▼] [Save Layout] [Reset]                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  PRESETS:                                                            │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 🗺️ Investigation  │ Default layout optimized for investigation│  │
│  │ ┌────────┬───────────────────────────────┬────────┐          │   │
│  │ │Filters │        Map/Canvas             │Details │          │   │
│  │ │        │                               │        │          │   │
│  │ │        │                               │        │          │   │
│  │ ├────────┴───────────────────────────────┤        │          │   │
│  │ │            Event Stream                 │        │          │   │
│  │ └──────────────────────────────────────────┴────────┘          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 📊 Analysis       │ Maximized canvas for detailed analysis    │  │
│  │ ┌────────────────────────────────────────────────────────┐  │   │
│  │ │                                                        │  │   │
│  │ │                     Full Canvas                        │  │   │
│  │ │                                                        │  │   │
│  │ │                                                        │  │   │
│  │ │                                                        │  │   │
│  │ └────────────────────────────────────────────────────────┘  │   │
│  │ [Floating panels: Filters ▼] [Details ▼] [Event Stream ▼] │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 📝 Review         │ Side-by-side for comparing items         │  │
│  │ ┌─────────────┬─────────────────┬─────────────────────┐     │   │
│  │ │  Filters   │   Item A         │    Item B           │     │   │
│  │ │             │   [Preview]     │    [Preview]        │     │   │
│  │ │             │   [Details]     │    [Details]        │     │   │
│  │ └─────────────┴─────────────────┴─────────────────────┘     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Responsive Layouts

### Tablet (768px - 1200px)

```
┌──────────────────────────────────────────────────────────────────────┐
│  [☰ Menu] Trace Controls (simplified) │ View: [🗺️] [📅] [▤]        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                    Map / Canvas (Full Width)                        │
│                                                                      │
│                    ┌─────────────────────────┐                       │
│                    │                         │                       │
│                    │      ●────●────●        │                       │
│                    │     /                   │                       │
│                    │    ●                    │                       │
│                    │              ●────────●  │                       │
│                    │                         │                       │
│                    │      ●                  │                       │
│                    │                         │                       │
│                    └─────────────────────────┘                       │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│  Active Filters: [× Devices: 2] [× 2025] [Clear All]               │
├──────────────────────────────────────────────────────────────────────┤
│  Event Stream (horizontal scroll)                                   │
│  [📷] [📷] [📷] [📷] [📷] [📷] [📷] [📷] [📷] [📷] →           │
└──────────────────────────────────────────────────────────────────────┘

Filter Palette: Bottom sheet (swipe up to reveal)
Details Panel: Full-screen modal (tap item to open)
```

### Mobile (< 768px)

```
┌────────────────────────────────────┐
│ [☰] Trace      [🔍] [⚙] [👤]     │
├────────────────────────────────────┤
│                                    │
│     Map / Canvas (Full Screen)     │
│                                    │
│     ┌─────────────────────────┐    │
│     │                         │    │
│     │      ●────●────●        │    │
│     │     /                   │    │
│     │    ●                    │    │
│     │             ●────────●  │    │
│     │                         │    │
│     │      ●                  │    │
│     │                         │    │
│     └─────────────────────────┘    │
│                                    │
│     [▶] [⏸] │ [━━━━━━━━●━━━]     │
│                                    │
├────────────────────────────────────┤
│  [📷] [📷] [📷] [📷] [📷] →     │
│  (thumbnail strip)                 │
├────────────────────────────────────┤
│                                    │
│  Filter Pills: [×2] [×1] [×3]    │
│  [Filter Button] 3,214 items      │
│                                    │
│  ──────────────────────────────   │
│  Bottom Sheet (slide up for full)  │
│  ┌────────────────────────────────┐│
│  │  Filter Palette               ││
│  │  ☑ Devices  ☑ Sources        ││
│  │  ☑ Types    ☐ Collections    ││
│  │  [Apply] [Clear]             ││
│  └────────────────────────────────┘│
└────────────────────────────────────┘
```

---

## Component Specifications

### Color Palette

| Element | Light Mode | Dark Mode | Usage |
|---------|-----------|----------|-------|
| Background Primary | #FFFFFF | #1a1a1a | Main canvas |
| Background Secondary | #F5F5F5 | #242424 | Panels |
| Background Tertiary | #EBEBEB | #333333 | Hover states |
| Border | #E0E0E0 | #404040 | Dividers |
| Text Primary | #212121 | #FFFFFF | Headings |
| Text Secondary | #757575 | #B3B3B3 | Labels |
| Accent Primary | #1976D2 | #64B5F6 | Buttons, links |
| Accent Secondary | #388E3C | #81C784 | Success, GPS |
| Warning | #F57C00 | #FFB74D | Deprecation |
| Error | #D32F2F | #EF5350 | Errors, delete |
| Map Marker | #1976D2 | #64B5F6 | Default |
| Map Route | #4CAF50 | #81C784 | Trace path |
| Cluster | #FF9800 | #FFB74D | Grouped items |

### Typography

| Element | Font | Size | Weight | Line Height |
|---------|------|------|--------|-------------|
| Page Title | Inter | 24px | 600 | 1.2 |
| Section Header | Inter | 16px | 600 | 1.3 |
| Body Text | Inter | 14px | 400 | 1.5 |
| Label | Inter | 12px | 500 | 1.4 |
| Caption | Inter | 11px | 400 | 1.3 |
| Monospace | JetBrains Mono | 12px | 400 | 1.4 |

### Spacing System

```
Base Unit: 4px

xs:  4px   (0.25rem)
sm:  8px   (0.5rem)
md:  16px  (1rem)
lg:  24px  (1.5rem)
xl:  32px  (2rem)
xxl: 48px  (3rem)
```

### Animation Specifications

| Animation | Duration | Easing | Usage |
|-----------|----------|--------|-------|
| Panel slide | 200ms | ease-out | Show/hide panels |
| Fade in/out | 150ms | ease-in-out | Tooltips, modals |
| Hover | 100ms | linear | Button hover states |
| Map marker bounce | 400ms | ease-out | New item highlight |
| Route draw | 1000ms | ease-in-out | Path animation |
| Cluster expand | 300ms | spring | Click to expand cluster |

---

## Navigation Recommendation

### Before (Current)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Librarian                                                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ Explorer│ │ Timeline │ │   Map    │ │ Entities │ │Relationships│   │
│  │          │ │          │ │          │ │          │ │          │   │
│  │  📁      │ │  📅      │ │  🗺️      │ │  👤      │ │  🔗      │   │
│  │          │ │          │ │          │ │          │ │          │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│      ●            ○            ○            ○            ○         │
│                                                                      │
│  CURRENT: Explorer (file browser)                                   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### After (Proposed)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Librarian                                                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ Explorer│ │  Trace   │ │ Entities │ │Relationships│ │Operations│   │
│  │          │ │          │ │          │ │          │ │          │   │
│  │  📁      │ │  🧭      │ │  👤      │ │  🔗      │ │  ⚙️      │   │
│  │          │ │          │ │          │ │          │ │          │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│      ●            ○            ○            ○            ○         │
│                                                                      │
│  PROPOSED: Explorer (file browser)                                   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Navigation Comparison

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Concept Count** | 5 | 5 | Equivalent |
| **Spatial-Temporal** | Separate (Timeline + Map) | Unified (Trace) | ✅ 2 → 1 |
| **Cognitive Load** | Must switch views | Single workspace | ✅ Reduced |
| **Terminology** | Timeline, Map | Trace | ✅ Consistent |
| **Flexibility** | Fixed views | Unified workspace | ✅ Improved |
| **Professionalism** | Consumer-oriented | Investigation-focused | ✅ Improved |

### Why Trace > Timeline + Map

1. **Unified Mental Model** — Users think "Trace" not "Timeline or Map"
2. **Reduced Navigation** — No switching between tabs
3. **Better Investigation** — Correlate time and space simultaneously
4. **Professional Terminology** — "Trace" fits forensic/investigative contexts
5. **Future-Proof** — Trace can include future dimensions (networks, timelines, etc.)

### Recommended Navigation Structure

```
Librarian
│
├── Explorer          # File browser (collection-based)
│   ├── Collections
│   ├── Folders
│   └── Favorites
│
├── Trace             # UNIFIED: Spatial-temporal investigation workspace
│   ├── Filter Palette
│   ├── Map Canvas
│   ├── Timeline View
│   ├── Playback Controls
│   └── Event Stream
│
├── Entities          # Person and place database
│   ├── People
│   ├── Places
│   └── Objects
│
├── Relationships     # Connection graph
│   ├── Network View
│   └── Import/Export
│
└── Operations        # Processing and utilities
    ├── Import
    ├── Export
    ├── Processing
    └── Settings
```

---

## Interaction Patterns

### Selection

```
Single Click → Select item (highlight in all views)
Ctrl+Click → Add to selection
Shift+Click → Range select
Double Click → Open detail view
Right Click → Context menu
```

### Drag & Drop

```
Drag item → Move to collection
Drag to canvas → Add to Trace
Drag selection → Batch move
Drag filter → Reorder
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Space` | Play/Pause playback |
| `←` / `→` | Previous/Next item |
| `Shift+←` / `Shift+→` | Skip 10 items |
| `Home` / `End` | First/Last item |
| `Ctrl+F` | Open filter palette |
| `Ctrl+S` | Save current Trace |
| `Ctrl+E` | Export Trace |
| `F11` | Toggle fullscreen |
| `1-4` | Switch view mode (Map/Timeline/Trace/Grid) |
| `+` / `-` | Zoom in/out |
| `[` / `]` | Decrease/Increase playback speed |

---

## Implementation Checklist

### Phase 1: Layout Foundation
- [ ] Grid layout system
- [ ] Panel component (collapsible, resizable)
- [ ] Sidebar component (left, right)
- [ ] Bottom panel component (event stream)
- [ ] Toolbar component

### Phase 2: Trace Components
- [ ] FilterPalette component
- [ ] MapCanvas component
- [ ] TimelineView component
- [ ] PlaybackControls component
- [ ] EventStream component

### Phase 3: Details Panel
- [ ] DetailsPanel component
- [ ] Thumbnail component
- [ ] Metadata display
- [ ] Tag editor
- [ ] Related items list

### Phase 4: Advanced Features
- [ ] Dockable panels
- [ ] Layout presets
- [ ] Fullscreen mode
- [ ] Responsive layouts
- [ ] Keyboard navigation

---

*UI Layout specification complete. Ready for design system implementation.*