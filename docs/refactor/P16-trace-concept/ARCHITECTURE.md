# ARCHITECTURE.md — Trace Unified Data Model

## Overview

Trace unifies temporal and spatial dimensions into a single conceptual model. This document defines the Trace architecture, its components, and how they relate to existing data structures.

## Unified Trace Model

```
┌─────────────────────────────────────────────────────────────────────┐
│                            TRACE                                    │
│                                                                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │   ID    │  │   Time  │  │ Location│  │  Device │  │Collection│  │
│  │         │  │         │  │         │  │         │  │         │   │
│  │ uuid    │  │ captured│  │ lat/lng │  │ source  │  │ folder  │   │
│  │ hash    │  │ created │  │ altitude│  │ make    │  │ album   │   │
│  │         │  │ modified│  │ address │  │ model   │  │ project │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
│       │            │            │            │            │        │
│       └────────────┴─────┬───────┴────────────┴────────────┘        │
│                          │                                          │
│                          ▼                                          │
│                 ┌─────────────────┐                                  │
│                 │  TRACE ITEM     │                                  │
│                 │                 │                                  │
│                 │  • artifact_id  │                                  │
│                 │  • timestamp    │                                  │
│                 │  • coordinates  │                                  │
│                 │  • device_info  │                                  │
│                 │  • collection   │                                  │
│                 └────────┬────────┘                                  │
│                          │                                          │
│                          ▼                                          │
│  ┌─────────┐  ┌─────────┐ │ ┌─────────┐  ┌─────────┐               │
│  │  Tags   │  │ Entity  │ │ │Relationship│ │ Metadata │            │
│  │         │  │         │ │ │          │  │          │               │
│  │ label   │  │ person  │ │ │ linked   │  │ exif     │               │
│  │ value   │  │ place    │ │ │ derived  │  │ custom   │               │
│  │ source  │  │ object   │ │ │ related  │  │ computed │               │
│  └─────────┘  └─────────┘ │ └─────────┘  └─────────┘               │
│                          │                                          │
│                          ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                        TRACE QUERY                           │   │
│  │                                                              │   │
│  │  Filter by: Time, Location, Device, Collection, Tags,       │   │
│  │            Entities, Relationships, Artifact Types           │   │
│  │                                                              │   │
│  │  Order by: Timestamp, Distance, Relevance, Cluster           │   │
│  │                                                              │   │
│  │  Group by: Time, Location, Device, Collection, Tags          │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Definitions

### 1. Trace (Collection)

A Trace is a filtered, ordered, grouped view of Trace Items.

```
Trace {
  id: UUID
  name: string
  description: string
  created_at: timestamp
  updated_at: timestamp
  created_by: user_id
  
  // Filter state
  filters: FilterState
  sort_order: SortOrder
  grouping: GroupingMode
  
  // View state
  viewport: Viewport (time range + geographic bounds)
  zoom_level: number
  playback_position: timestamp | null
  
  // Computed
  item_count: number
  bounds: GeoBounds
  time_range: TimeRange
}
```

### 2. Trace Item (Artifact Instance)

A Trace Item is an artifact with its spatial-temporal properties fully resolved.

```
TraceItem {
  id: UUID
  artifact_id: UUID  // Reference to source artifact
  
  // Time properties
  time: TimeProperties {
    captured_at: timestamp
    created_at: timestamp
    modified_at: timestamp
    
    // Computed
    time_offset: duration      // From trace start
    time_cluster: string       // Grouping key (e.g., "2026-01")
  }
  
  // Location properties
  location: LocationProperties {
    coordinates: Coordinates {
      latitude: float
      longitude: float
      altitude: float | null
      accuracy: float | null
    }
    
    // Geocoded
    address: Address | null
    place_name: string | null
    
    // Semantic
    semantic_location: string | null  // "Home", "Office", "Airport"
    
    // Computed
    location_cluster: string          // Geohash or similar
    distance_from_origin: float
  }
  
  // Source properties
  device: DeviceProperties {
    source: DeviceSource | enum
    make: string | null
    model: string | null
    serial: string | null
    
    // Type categorization
    device_type: DeviceType | enum
    // "smartphone", "dslr", "drone", "webcam", "scanner", etc.
  }
  
  // Collection properties
  collection: CollectionProperties {
    folder_path: string
    album_name: string | null
    project: string | null
    collection_id: UUID
    
    // Hierarchy
    collection_path: string[]  // ["Camera", "2026", "January"]
  }
  
  // Annotation properties
  tags: TagProperties {
    labels: Tag[]
    // Tag {
    //   name: string
    //   value: string | null
    //   source: TagSource | enum
    //   confidence: float | null
    // }
  }
  
  // Entity recognition
  entities: EntityProperties {
    people: Entity[]   // Detected faces, named people
    places: Entity[]   // Recognized locations
    objects: Entity[]   // Detected objects
    logos: Entity[]    // Recognized brands/logos
  }
  
  // Relationships
  relationships: RelationshipProperties {
    links: Relationship[]
    // Relationship {
    //   target_id: UUID
    //   type: RelationshipType | enum
    //   confidence: float
    // }
    
    // Computed types
    derived_from: UUID | null    // Parent/original
    linked_to: UUID[]            // Related artifacts
    grouped_with: UUID[]         // Same burst/series
  }
  
  // Metadata
  metadata: MetadataProperties {
    file_type: FileType | enum
    mime_type: string
    size_bytes: integer
    dimensions: Dimensions | null
    
    // Computed
    importance_score: float      // For sorting/filtering
    anomaly_score: float         // For flagging unusual items
  }
}
```

### 3. Time Component

Temporal intelligence for trace analysis.

```
TimeProperties {
  // Primary timestamps
  captured_at: timestamp        // When the artifact was created
  created_at: timestamp         // When file was created
  modified_at: timestamp        // When file was modified
  
  // Granularity
  time_of_day: TimeOfDay | enum // "morning", "afternoon", "evening", "night"
  day_of_week: integer          // 0-6
  season: Season | enum         // "spring", "summer", "fall", "winter"
  
  // Computed
  time_offset: duration         // Relative to trace start
  time_cluster: string          // Grouping key
  time_gap: duration            // Gap from previous item
  time_density: float            // Items per hour in this cluster
}
```

### 4. Location Component

Spatial intelligence for geographic analysis.

```
LocationProperties {
  // Raw coordinates
  coordinates: Coordinates {
    latitude: float
    longitude: float
    altitude: float | null
    accuracy: float | null
    heading: float | null
    speed: float | null
  }
  
  // Geocoding
  reverse_geocoded: ReverseGeocodedAddress {
    street_number: string
    street_name: string
    city: string
    state: string
    postal_code: string
    country: string
    formatted_address: string
  }
  
  // Semantic location
  semantic_location: SemanticLocation {
    label: string               // "Home", "Office", "Gym"
    type: PlaceType | enum
    confidence: float
    source: string              // "user", "ai", "foursquare", etc.
  }
  
  // Clustering
  geohash: string               // Geohash for clustering
  cluster_id: UUID | null       // Associated cluster
  cluster_center: Coordinates   // Cluster centroid
  
  // Computed
  distance_from_previous: float // Distance from last item
  distance_from_first: float    // Total distance traveled
  speed_between_points: float   // Computed speed
  location_entropy: float      // Diversity measure
}
```

### 5. Device Component

Device identification and categorization.

```
DeviceProperties {
  // Source identification
  source: DeviceSource | enum {
    gps_exif        // GPS data from EXIF
    wifi_geolocation // WiFi-based location
    cell_tower      // Cell tower triangulation
    manual          // User-entered
    ip_geolocation  // IP-based
    ocr             // OCR from document
    api             // From external API
  }
  
  // Device details
  device_id: string | null
  make: string | null           // "Apple", "Samsung", "Canon"
  model: string | null          // "iPhone 15", "Galaxy S24", "EOS R5"
  serial: string | null         // Serial number if available
  lens: string | null          // Lens info for cameras
  
  // Categorization
  device_type: DeviceType | enum {
    smartphone
    tablet
    dslr
    mirrorless
    action_camera
    drone
    security_camera
    webcam
    scanner
    radar
    lidar
    other
  }
  
  // Computed
  device_category: string      // Grouped type
  is_mobile: boolean
  has_gps: boolean
  has_wifi: boolean
}
```

### 6. Collection Component

Hierarchical organization of artifacts.

```
CollectionProperties {
  // Path components
  collection_id: UUID
  root_collection: string       // "Camera", "Documents", "Evidence"
  folder_path: string           // Full path
  folder_name: string           // Current folder
  file_name: string             // Original filename
  
  // Album/Project
  album_name: string | null
  project_name: string | null
  tags: string[]               // Folder-based tags
  
  // Hierarchy
  collection_level: integer     // Depth in hierarchy
  parent_collection_id: UUID | null
  child_collection_ids: UUID[]
  
  // Computed
  is_root: boolean
  item_count: integer          // Items in this collection
}
```

### 7. Tags Component

Labeling and annotation system.

```
TagProperties {
  tags: Tag[]
  
  // Tag structure
  // name: string              // Tag identifier
  // value: string | null      // Tag value (e.g., "important", "reviewed")
  // source: TagSource | enum  // Where tag came from
  // confidence: float | null  // AI confidence if auto-generated
  // created_at: timestamp
  // created_by: user_id | null
  
  // Tag sources
  tag_sources: TagSource[] | enum {
    user              // Manually added by user
    exif              // Extracted from EXIF/metadata
    ocr               // Extracted via OCR
    ai_detection     // AI-generated
    semantic_location // From location semantics
    face_detection    // From face recognition
    object_detection  // From object detection
    api               // From external API
    import            // From import process
  }
  
  // Computed
  tag_count: integer
  unique_tag_names: string[]
  tag_categories: string[]      // Grouped tags
}
```

### 8. Entity Component

Recognized entities within artifacts.

```
EntityProperties {
  // People
  people: PersonEntity[] {
    face_id: UUID | null
    name: string | null
    confidence: float
    bounding_box: BoundingBox | null
    known: boolean              // In known persons database
  }
  
  // Places
  places: PlaceEntity[] {
    place_id: string | null    // POI identifier
    name: string
    type: PlaceType | enum
    coordinates: Coordinates | null
    confidence: float
  }
  
  // Objects
  objects: ObjectEntity[] {
    label: string
    confidence: float
    bounding_box: BoundingBox
    category: string
  }
  
  // Logos
  logos: LogoEntity[] {
    brand: string
    confidence: float
    bounding_box: BoundingBox
  }
  
  // Computed
  entity_count: integer
  primary_entity: Entity | null
  entity_types: string[]
}
```

### 9. Relationships Component

Connections between artifacts.

```
RelationshipProperties {
  // Explicit relationships
  relationships: Relationship[] {
    target_id: UUID
    type: RelationshipType | enum
    bidirectional: boolean
    confidence: float
    source: RelationshipSource | enum
    metadata: object | null
  }
  
  // Relationship types
  relationship_types: RelationshipType[] | enum {
    // Temporal
    same_burst          // Same photo burst
    same_panorama       // Part of same panorama
    same_timelapse      // Part of same timelapse
    consecutive         // Sequential shots
    
    // Spatial
    same_location       // Within proximity threshold
    same_route          // Along same path
    nearby              // Proximity relationship
    
    // Content
    similar_content     // Visually similar
    duplicate           // Duplicate detection
    contains            // Container/content relationship
    
    // Semantic
    same_event          // Same event/activity
    same_person         // Same detected person
    same_project        // Same project
    references          // References another artifact
    
    // Derived
    derived_from        // Processed/edited from
    version_of          // Version relationship
    reply_to            // Response relationship
    
    // Custom
    custom              // User-defined
  }
  
  // Computed
  relationship_count: integer
  outgoing_count: integer
  incoming_count: integer
  connected_items: UUID[]       // All directly connected
  network_position: float      // Centrality measure
}
```

## Query Interface

### Filter State

```
FilterState {
  // Time filters
  time_range: TimeRange | null
  // TimeRange { start: timestamp, end: timestamp }
  
  time_of_day: TimeOfDay[] | null
  day_of_week: integer[] | null
  season: Season[] | null
  
  // Location filters
  geographic_bounds: GeoBounds | null
  // GeoBounds { north: float, south: float, east: float, west: float }
  
  radius: RadiusFilter | null
  // RadiusFilter { center: Coordinates, radius_km: float }
  
  semantic_locations: string[] | null
  location_clusters: UUID[] | null
  
  // Device filters
  device_types: DeviceType[] | null
  device_ids: string[] | null
  device_makes: string[] | null
  
  // Collection filters
  collection_ids: UUID[] | null
  collection_paths: string[] | null
  root_collections: string[] | null
  
  // Tag filters
  tags: TagFilter | null
  // TagFilter { include: string[], exclude: string[], match_all: boolean }
  
  // Entity filters
  entity_filters: EntityFilter | null
  // EntityFilter { people: string[], places: string[], objects: string[] }
  
  // Relationship filters
  related_to: UUID | null
  relationship_types: RelationshipType[] | null
  
  // Artifact type filters
  file_types: FileType[] | null
  
  // Computed filters
  importance_score_min: float | null
  anomaly_score_min: float | null
  
  // Search
  search_query: string | null
  search_fields: string[] | null
}
```

### Sort Options

```
SortOrder {
  field: SortField | enum {
    captured_at
    created_at
    modified_at
    distance_from_start
    importance_score
    relevance
    collection_path
    device_model
  }
  
  direction: SortDirection | enum {
    ascending
    descending
  }
}
```

### Grouping Modes

```
GroupingMode {
  type: GroupingType | enum {
    none                    // Flat list
    time_cluster            // Group by time proximity
    geographic_cluster      // Group by location proximity
    collection              // Group by collection
    device                  // Group by device
    semantic_location       // Group by place type
    entity                  // Group by detected entities
    date                    // Group by calendar date
    month                   // Group by month
    year                    // Group by year
  }
  
  collapsed_by_default: boolean
  sort_within_group: SortOrder
}
```

## Viewport State

```
Viewport {
  // Geographic viewport
  center: Coordinates
  zoom: float
  bounds: GeoBounds
  
  // Temporal viewport
  time_center: timestamp
  time_span: duration
  
  // View mode
  mode: ViewMode | enum {
    map                     // Map-centric view
    timeline                // Timeline-centric view
    split                   // Side-by-side split
    trace                   // Unified trace canvas
  }
  
  // Overlay visibility
  show_clusters: boolean
  show_routes: boolean
  show_heatmaps: boolean
  show_labels: boolean
  show_trails: boolean
}
```

## API Contracts

### Trace Query API

```typescript
// GET /api/traces
interface ListTracesRequest {
  filters?: FilterState;
  sort?: SortOrder;
  group?: GroupingMode;
  pagination?: {
    offset: number;
    limit: number;
  };
}

interface ListTracesResponse {
  traces: Trace[];
  total_count: number;
  filtered_count: number;
}

// GET /api/traces/:id/items
interface GetTraceItemsRequest {
  trace_id: UUID;
  filters?: FilterState;
  sort?: SortOrder;
  group?: GroupingMode;
  pagination?: {
    offset: number;
    limit: number;
  };
  include_relationships?: boolean;
  include_entities?: boolean;
}

interface GetTraceItemsResponse {
  items: TraceItem[];
  total_count: number;
  filtered_count: number;
  bounds: GeoBounds;
  time_range: TimeRange;
}

// POST /api/traces
interface CreateTraceRequest {
  name: string;
  description?: string;
  filters?: FilterState;
  sort?: SortOrder;
  group?: GroupingMode;
}

interface CreateTraceResponse {
  trace: Trace;
}

// PATCH /api/traces/:id
interface UpdateTraceRequest {
  name?: string;
  description?: string;
  filters?: FilterState;
  sort?: SortOrder;
  group?: GroupingMode;
  viewport?: Viewport;
}

interface UpdateTraceResponse {
  trace: Trace;
}
```

## Performance Considerations

### Indexing Strategy

For efficient Trace queries:

1. **Time Index** — B-tree index on `captured_at`
2. **Geospatial Index** — R-tree or Quadtree on coordinates
3. **Composite Indexes** — (time, location), (device, time), (collection, time)
4. **Full-Text Index** — On tags, entities, search fields
5. **Cluster Index** — Pre-computed clusters for common groupings

### Pagination Strategy

1. **Cursor-based pagination** — For stable iteration
2. **Keyset pagination** — For sorted queries
3. **Virtual scrolling** — For UI performance
4. **Lazy loading** — Load clusters first, expand on demand

### Aggregation Pipeline

For dashboard/statistics queries:

```sql
SELECT 
  date_trunc('month', captured_at) as month,
  device_type,
  COUNT(*) as item_count,
  AVG(importance_score) as avg_importance
FROM trace_items
WHERE filters...
GROUP BY month, device_type
ORDER BY month DESC
```

## Security Model

### Access Control

```
TraceAccess {
  trace_id: UUID
  user_id: UUID
  permission: Permission | enum {
    view
    edit
    admin
    share
  }
  
  // Scope
  scope: AccessScope | enum {
    all         // Full access to all items
    filtered    // Access to filtered subset only
    collection  // Access to specific collection
  }
}
```

---

*Architecture supports unified spatial-temporal querying with scalable, secure access control.*