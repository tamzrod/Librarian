# FILTERS.md — Node-RED Inspired Filter Palette System

## Overview

Trace uses a **palette-based filter system** inspired by Node-RED's visual programming interface. Filters are organized into collapsible categories, displayed as checkbox lists, and combined using AND logic within categories and OR logic across selections within a category.

## Design Philosophy

### Node-RED Inspiration

Node-RED provides:
- Visual flow-based programming
- Palette of nodes/categories
- Drag-and-drop composition
- Real-time filtering
- Visual feedback

Trace Filter Palette:
- Visual category-based filtering
- Checkbox-based selection
- Collapsible sections
- Active filter indicators
- Real-time results update

### Core Principles

1. **Speed Over Completeness** — Show the most common filters first
2. **Visual Feedback** — Clear indication of active filters and result counts
3. **Progressive Disclosure** — Advanced filters hidden by default
4. **Touch-Friendly** — Large tap targets for mobile/tablet use
5. **Keyboard Accessible** — Full keyboard navigation support

## Filter Palette Layout

```
┌──────────────────────────────────────────────────────────────┐
│  🔍 Filter Palette                          [Clear All] × │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ▼ DEVICES                                          3/5 │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  ☑ HONOR BRP-NX1                            (1,247)   │ │
│  │  ☑ Xiaomi 2109119DG                            (892)   │ │
│  │  ☐ iPhone                                      (0)     │ │
│  │  ☐ DJI Drone                                   (156)   │ │
│  │  ☐ Canon DSLR                                  (43)    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ▼ SOURCES                                           2/4│ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  ☑ GPS EXIF                                   (2,156) │ │
│  │  ☑ OCR                                        (312)    │ │
│  │  ☐ Manual Tag                                 (89)    │ │
│  │  ☐ Semantic Location                          (445)    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ▼ ARTIFACT TYPES                                     3/4│
│  ├────────────────────────────────────────────────────────┤ │
│  │  ☑ Images                                    (2,890) │ │
│  │  ☑ Video                                       (267)  │ │
│  │  ☐ Documents                                    (45)   │ │
│  │  ☑ Audio                                       (12)   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ▼ COLLECTIONS                                        2/8│
│  ├────────────────────────────────────────────────────────┤ │
│  │  ☑ Camera Roll                               (2,156) │ │
│  │  ☑ Evidence                                   (312)  │ │
│  │  ☐ Project Alpha                              (156)   │ │
│  │  ☐ Project Beta                                (89)   │ │
│  │  ☐ Archive 2024                              (234)   │ │
│  │  ☐ Archive 2023                              (567)   │ │
│  │  ☐ Archive 2022                              (345)   │ │
│  │  ☐ Import Queue                                (23)   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ▼ TIME RANGE                                           │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  [2023] [2024] [2025] [2026]                          │ │
│  │  Custom: [From: _________] [To: _________]            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ▶ LOCATION (click to expand map filter)                │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ▶ TAGS (click to expand tag filter)                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ▶ ENTITIES (click to expand entity filter)             │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ▶ ADVANCED (click to expand advanced options)          │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  ☑ Include items without location                     │ │
│  │  ☑ Include items without timestamp                     │ │
│  │  Importance: [────●─────] min: 0.3                   │ │
│  │  Anomaly Score: [─────●───] min: 0.5                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Showing 3,214 of 3,891 items          [Apply Filters]     │
└──────────────────────────────────────────────────────────────┘
```

## Filter Categories

### 1. Devices

Filter by capture device.

```
Category: Devices
State: Expanded (default for < 10 devices)
Max Visible: 5 items + "Show more"
Sort: By count (descending)

Selection Mode: Multi-select checkbox
Logic: OR within category (any selected device)

States:
☑ Selected (include in results)
☐ Unselected (exclude from results)
```

**Example:**
```
☑ HONOR BRP-NX1        (1,247 items)
☑ Xiaomi 2109119DG     (892 items)
☐ iPhone               (0 items)
☐ DJI Drone            (156 items)
☐ Canon DSLR           (43 items)

Result: Items from HONOR OR Xiaomi devices
```

### 2. Sources

Filter by location data source.

```
Category: Sources
State: Collapsed (default)
Max Visible: 4 items
Sort: By count (descending)

Sources:
- GPS EXIF         (from image metadata)
- OCR              (from document scanning)
- Manual Tag       (user-entered)
- Semantic Location (AI-inferred)
- WiFi Geolocation
- Cell Tower
- IP Geolocation
- API Import
```

**Example:**
```
☑ GPS EXIF           (2,156 items)
☐ OCR                (312 items)
☑ Manual Tag         (89 items)
☐ Semantic Location  (445 items)

Result: Items with GPS EXIF OR Manual Tag sources
```

### 3. Artifact Types

Filter by file type.

```
Category: Artifact Types
State: Expanded (default)
Max Visible: 5 items
Sort: By count (descending)

Types:
- Images       (jpg, png, webp, heic, gif, bmp, tiff)
- Video        (mp4, mov, avi, mkv, webm)
- Documents     (pdf, doc, docx, txt, rtf)
- Audio         (mp3, wav, aac, flac, ogg)
- Archives      (zip, rar, 7z, tar)
```

**Example:**
```
☑ Images         (2,890 items)
☑ Video          (267 items)
☐ Documents      (45 items)
☑ Audio          (12 items)

Result: Images OR Video OR Audio files
```

### 4. Collections

Filter by collection/folder.

```
Category: Collections
State: Collapsed (default)
Max Visible: 5 items + item count
Sort: By count (descending)
Hierarchy: Tree view with expand/collapse

Features:
- Checkbox with hierarchical selection
- Child selection propagates to parent (optional)
- Virtual scrolling for large lists
- Search within collections
```

**Example:**
```
☑ Camera Roll            (2,156 items)
  ├─ 📁 2026              (890 items)
  │   ├─ 📁 January       (234 items)
  │   └─ 📁 February      (456 items)
  ├─ 📁 2025              (1,234 items)
  └─ 📁 2024              (432 items)
☑ Evidence               (312 items)
  ├─ 📁 Case-001          (156 items)
  └─ 📁 Case-002          (156 items)
☐ Project Alpha          (89 items)

Result: Camera Roll OR Evidence collection
```

### 5. Time Range

Filter by temporal bounds.

```
Category: Time Range
State: Expanded (default)
Display: Quick select chips + custom range

Quick Select:
[2023] [2024] [2025] [2026] [All Time] [Custom]

Custom Range:
From: [Date Picker] [Time Picker]
To:   [Date Picker] [Time Picker]

Granularity Options:
○ By Year
○ By Month
○ By Week
○ By Day
○ Exact timestamps
```

**Example:**
```
Quick: [2023] [2024] [☑2025] [2026]

Custom:
From: [Jan 1, 2025 ▾] [09:00 ▾]
To:   [Dec 31, 2025 ▾] [18:00 ▾]

Result: Items captured in 2025
```

### 6. Location (Expanded)

Geographic filtering with map.

```
Category: Location
State: Collapsed (click to expand)
Display: Map preview + filter controls

Expanded View:
┌─────────────────────────────────────────────────────────────┐
│  Location Filter                                       [×] │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    MAP CANVAS                         │  │
│  │                                                      │  │
│  │     ┌─────────────────────────────────┐              │  │
│  │     │   Selected Region               │              │  │
│  │     │   (blue rectangle)              │              │  │
│  │     └─────────────────────────────────┘              │  │
│  │                                                      │  │
│  │   ○ Draw Rectangle  ○ Draw Circle  ○ Draw Polygon   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  Radius Filter:                                            │
│  Center: [40.7128, -74.0060]                               │
│  Radius: [======●=====] 50 km                             │
│                                                             │
│  Semantic Locations:                                       │
│  ☐ Home  ☐ Work  ☐ School  ☐ Custom...                   │
│                                                             │
│  [Apply Region] [Clear]                                   │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Draw on map to select region
- Radius filter from center point
- Polygon selection for complex shapes
- Semantic location tags (Home, Work, etc.)
- Address search

### 7. Tags

Filter by custom labels.

```
Category: Tags
State: Collapsed (click to expand)
Display: Tag chips + search

Expanded View:
┌─────────────────────────────────────────────────────────────┐
│  Tag Filter                                    [Search...] │
├─────────────────────────────────────────────────────────────┤
│  Match Mode: ○ Include any  ○ Include all  ○ Exclude      │
│                                                             │
│  Selected Tags:                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ [important ×] [+research ×] [+reviewed ×]          │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Available Tags:                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 🔵 important          (234)     ☐ Include           │  │
│  │ 🟢 +research          (156)     ☑ Include           │  │
│  │ 🟡 +reviewed          (89)      ☑ Include           │  │
│  │ 🔴 flagged            (45)      ☐ Exclude            │  │
│  │ ⚪ to-share            (23)      ☐ Include           │  │
│  │ 🔵 evidence           (312)     ☐ Include           │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  [Apply Tags] [Clear]                                      │
└─────────────────────────────────────────────────────────────┘
```

**Tag Color Coding:**
- 🔵 Blue: User-applied tags
- 🟢 Green: AI-suggested tags
- 🟡 Yellow: Review-pending tags
- 🔴 Red: Flagged/excluded tags
- ⚪ Gray: System tags

### 8. Entities

Filter by detected entities.

```
Category: Entities
State: Collapsed (click to expand)
Sub-categories: People, Places, Objects

Expanded View:
┌─────────────────────────────────────────────────────────────┐
│  Entity Filter                                             │
├─────────────────────────────────────────────────────────────┤
│  ▼ PEOPLE (12 detected)                                    │
│    ☑ John Smith         (89 photos)   [Known ✓]           │
│    ☑ Jane Doe           (67 photos)   [Known ✓]           │
│    ☑ Unknown Person #1   (23 photos)   [Review needed]     │
│    ☐ Unknown Person #2   (12 photos)   [Review needed]     │
│                                                             │
│  ▼ PLACES (8 detected)                                     │
│    ☑ Times Square        (45 photos)                      │
│    ☐ Central Park       (34 photos)                      │
│    ☐ Empire State Bldg   (23 photos)                      │
│                                                             │
│  ▼ OBJECTS (45 categories)                                 │
│    ☐ Car                 (234)                            │
│    ☐ Dog                 (156)                            │
│    ☐ Bicycle             (89)                             │
│    ☐ ...                 (more)                           │
└─────────────────────────────────────────────────────────────┘
```

### 9. Advanced

Advanced filtering options.

```
Category: Advanced
State: Collapsed (click to expand)

Options:
┌─────────────────────────────────────────────────────────────┐
│  DATA COMPLETENESS                                        │
│  ☐ Include items without location                          │
│  ☐ Include items without timestamp                         │
│  ☐ Include items without device info                      │
│                                                             │
│  IMPORTANCE SCORING                                        │
│  Importance: [─────────●───] min: 0.30                    │
│  (0 = all items, 1 = most important only)                  │
│                                                             │
│  ANOMALY DETECTION                                         │
│  Anomaly Score: [─────────●───] min: 0.50                   │
│  (0 = all items, 1 = most anomalous only)                  │
│                                                             │
│  RELATIONSHIPS                                             │
│  ○ Show all items                                          │
│  ○ Show only related items                                 │
│  ○ Show only standalone items                              │
│                                                             │
│  Keyword Search: [________________________]                │
│  Search in: ☑ Filename ☐ Tags ☐ OCR ☐ Metadata            │
└─────────────────────────────────────────────────────────────┘
```

## Filter State Management

### URL Synchronization

Filters are synchronized with URL parameters for shareable views:

```
/trace?filters=devices:HONOR,Xiaomi&time=2025&types=Images,Video&collection=Evidence
```

**URL Parameter Mapping:**
```
devices=<device_ids_csv>
sources=<source_types_csv>
types=<artifact_types_csv>
collections=<collection_ids_csv>
time=<year>|<start_date>,<end_date>
location=<bounds>|<radius_center>,<radius_km>
tags=<tag_names_csv>
people=<person_ids_csv>
places=<place_ids_csv>
search=<query>
sort=<field>:<direction>
group=<grouping_type>
```

### Filter Persistence

- **Session Storage** — Filters persist during session
- **Local Storage** — Default filter preferences
- **User Preferences** — Saved filter presets
- **URL State** — Shareable filter configurations

### Filter Presets

```
┌─────────────────────────────────────────────────────────────┐
│  Filter Presets                                   [Save ▾]│
├─────────────────────────────────────────────────────────────┤
│  [★ Default] [★ My Presets ▾] [★ Shared ▾]                 │
│                                                             │
│  My Presets:                                                │
│  ├─ 📷 Smartphone Photos Only                        [▶] ││
│  ├─ 📅 Last 30 Days                                    [▶] ││
│  ├─ 🏠 Home & Work Locations                           [▶] ││
│  └─ 🔍 Evidence with Tags                              [▶] ││
│                                                             │
│  Shared:                                                    │
│  ├─ 👤 All Photos with John                            [▶] ││
│  └─ 📍 NYC Area                                         [▶] ││
└─────────────────────────────────────────────────────────────┘
```

## Visual Feedback

### Active Filter Indicators

```
┌─────────────────────────────────────────────────────────────┐
│  [Play] [Pause] [1x] [4x] [16x]          [Filters: 4 ▾]    │
├─────────────────────────────────────────────────────────────┤
│  Filter Pills:                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [× Devices: 2] [× Sources: 2] [× 2025] [× Types: 3]│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Click × to remove individual filter                       │
│  Click "Filters: 4" to open palette                        │
└─────────────────────────────────────────────────────────────┘
```

### Count Updates

```
As filters are applied:
┌─────────────────────────────────────────────────────────────┐
│  Devices                                                   │
│  ☑ HONOR BRP-NX1    (1,247 → 892)  ↓28%                  │
│  ☑ Xiaomi 2109119DG (892 → 534)    ↓40%                  │
│  ☐ iPhone           (0 → 0)        (hidden if 0)          │
└─────────────────────────────────────────────────────────────┘

Green: Filter increases count (expanded search)
Red: Filter decreases count (narrowed search)
Gray: No change
```

### Loading States

```
┌─────────────────────────────────────────────────────────────┐
│  Applying filters...                                       │
│  ████████████░░░░░░░░░░░░░░░░░  1,247 / 3,891 items       │
│                                                             │
│  [Cancel]                                                   │
└─────────────────────────────────────────────────────────────┘
```

## Accessibility

### Keyboard Navigation

```
Tab           → Move between filter sections
Enter/Space   → Toggle checkbox
Arrow Up/Down → Navigate within section
Arrow Left/Right → Collapse/Expand section
Escape        → Clear current filter / Close palette
Ctrl+/        → Open filter palette (global shortcut)
```

### Screen Reader Support

```
<FilterSection role="group" aria-labelledby="devices-header">
  <span id="devices-header">Devices</span>
  <span>3 of 5 selected</span>
  
  <checkbox role="checkbox" aria-checked="true">
    HONOR BRP-NX1, 1,247 items
  </checkbox>
</FilterSection>

<button aria-label="Clear all filters">Clear All</button>
```

### Focus Management

```
- Focus trap within palette when open
- Return focus to trigger when closed
- Skip link to results area
- Visible focus indicators
```

## Responsive Design

### Desktop (> 1200px)

```
┌──────────────────────────────────────────────────────────────┐
│  [Filters] [Sort ▾] [Group ▾]      [View ▾]  [Share]        │
├──────────────┬───────────────────────────────────────────────┤
│              │                                               │
│  Filter      │  Trace Canvas / Map / Timeline               │
│  Palette     │                                               │
│  (280px)     │                                               │
│              │                                               │
│  ┌─────────┐  │  ┌─────────────────────────────────────────┐│
│  │ Devices │  │  │                                         ││
│  ├─────────┤  │  │                                         ││
│  │ Sources │  │  │                                         ││
│  ├─────────┤  │  │                                         ││
│  │ Types   │  │  │                                         ││
│  └─────────┘  │  │                                         ││
│              │  └─────────────────────────────────────────┘│
│              │                                               │
└──────────────┴───────────────────────────────────────────────┘
```

### Tablet (768px - 1200px)

```
┌──────────────────────────────────────────────────────────────┐
│  [☰ Filters] [Sort ▾]        [View ▾]  [Share]            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Trace Canvas / Map / Timeline                              │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ [Active Filter Pills: ×2 ×1 ×3]              [Clear] │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                                                        │ │
│  │                                                        │ │
│  │                                                        │ │
│  │                                                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Bottom Sheet Filter Panel (slide up on tap)                │
└──────────────────────────────────────────────────────────────┘
```

### Mobile (< 768px)

```
┌────────────────────────────────────┐
│ [☰] [Sort ▾]     [View ▾] [Share] │
├────────────────────────────────────┤
│                                    │
│    Trace Canvas / Map / Timeline   │
│                                    │
│    ┌────────────────────────────┐ │
│    │                            │ │
│    │                            │ │
│    │                            │ │
│    │                            │ │
│    │                            │ │
│    └────────────────────────────┘ │
│                                    │
│  ┌──────────────────────────────┐ │
│  │ [×2] [×1] [×3] [Clear]       │ │
│  └──────────────────────────────┘ │
│                                    │
│  ┌────────────────────────────────┐│
│  │     [Filter Button]            ││
│  │     3,214 items               ││
│  └────────────────────────────────┘│
│                                    │
│  Filter Panel (Full screen modal) │
└────────────────────────────────────┘
```

## Filter API

### Filter State Object

```typescript
interface FilterState {
  devices?: {
    selected: string[];        // Device IDs
    mode: 'include' | 'exclude';
  };
  
  sources?: {
    selected: SourceType[];
    mode: 'include' | 'exclude';
  };
  
  artifactTypes?: {
    selected: FileType[];
    mode: 'include' | 'exclude';
  };
  
  collections?: {
    selected: string[];        // Collection IDs
    mode: 'include' | 'exclude' | 'hierarchy';
  };
  
  timeRange?: {
    preset?: 'all' | 'today' | 'week' | 'month' | 'year' | 'custom';
    start?: Date;
    end?: Date;
    granularity?: 'year' | 'month' | 'week' | 'day';
  };
  
  location?: {
    bounds?: GeoBounds;
    radius?: {
      center: Coordinates;
      radiusKm: number;
    };
    polygon?: Coordinates[];
    semanticLocations?: string[];
  };
  
  tags?: {
    selected: string[];
    matchMode: 'any' | 'all' | 'none';
  };
  
  entities?: {
    people?: string[];        // Person IDs
    places?: string[];         // Place IDs
    objects?: string[];        // Object labels
  };
  
  advanced?: {
    includeWithoutLocation?: boolean;
    includeWithoutTimestamp?: boolean;
    importanceMin?: number;
    anomalyMin?: number;
    relationships?: 'all' | 'related' | 'standalone';
    searchQuery?: string;
    searchFields?: ('filename' | 'tags' | 'ocr' | 'metadata')[];
  };
}
```

### API Endpoints

```typescript
// GET available filter options with counts
GET /api/traces/filters
Response: {
  devices: Array<{ id: string; name: string; count: number }>;
  sources: Array<{ type: SourceType; label: string; count: number }>;
  artifactTypes: Array<{ type: FileType; label: string; count: number }>;
  collections: Array<{ id: string; name: string; path: string[]; count: number }>;
  timeRange: { min: Date; max: Date; counts: Record<string, number> };
  locations: Array<{ name: string; type: string; count: number }>;
  tags: Array<{ name: string; color: string; count: number }>;
  entities: {
    people: Array<{ id: string; name: string; count: number; known: boolean }>;
    places: Array<{ id: string; name: string; count: number }>;
    objects: Array<{ label: string; count: number }>;
  };
}

// GET filtered trace items
GET /api/traces/:id/items?filters=<encoded_filter_state>&sort=<sort>&group=<grouping>

// POST save filter preset
POST /api/traces/filters/presets
Body: { name: string; filters: FilterState; scope: 'private' | 'shared' }

// GET filter presets
GET /api/traces/filters/presets
```

## Implementation Notes

### Performance Optimization

1. **Debounced Updates** — Wait 300ms after last filter change before querying
2. **Count Caching** — Cache counts per filter combination
3. **Incremental Loading** — Show results immediately, update counts in background
4. **Prefetching** — Anticipate likely filter combinations
5. **Web Workers** — Filter computation off main thread for large datasets

### Best Practices

1. **Default Filters** — Start with reasonable defaults (last 30 days, all types)
2. **Empty States** — Clear messaging when filters return no results
3. **Undo Support** — Easy way to revert accidental filter changes
4. **Filter Hints** — Suggest related filters when current selection is very narrow
5. **Batch Operations** — Support applying multiple filters at once

---

*Palette-based filtering: fast, visual, and powerful.*