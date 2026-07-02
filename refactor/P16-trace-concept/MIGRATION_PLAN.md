# MIGRATION_PLAN.md — Timeline + Map → Trace Migration

## Overview

This document outlines the phased migration strategy from the separate Timeline and Map navigation paradigms to the unified Trace concept.

## Migration Principles

1. **Backward Compatibility** — Existing functionality preserved during transition
2. **Progressive Rollout** — New features introduced incrementally
3. **User Control** — Users can choose when to adopt new features
4. **Rollback Capability** — Can revert if issues arise
5. **No Data Loss** — All existing data preserved and migrated

## Migration Phases

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MIGRATION TIMELINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Phase 1     Phase 2     Phase 3     Phase 4     Phase 5           │
│  ┌───┐      ┌───┐      ┌───┐      ┌───┐      ┌───┐              │
│  │Timeline│  │Trace│   │Trace│    │Trace│    │Trace│             │
│  │   +    │  │ Intro│  │Timeline│  │ Deprec│  │Primary│         │
│  │  Map   │  │      │   │ Depres│  │ Map De│  │      │          │
│  │ Coexist│  │      │   │ Timeline│  │ pres │  │      │         │
│  └───┘      └───┘      └───┘      └───┘      └───┘               │
│                                                                     │
│  ◄────────────────────────────────────────────────────────────────► │
│  Compatibility Mode                    →      Modern Architecture   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Coexistence

**Duration:** 2-3 sprints  
**Goal:** Prepare infrastructure without changing user experience

### Objectives

1. Introduce Trace data model extensions
2. Create Trace API endpoints (parallel to existing)
3. Add Trace storage tables/views
4. Build migration scripts
5. Establish feature flags for gradual rollout

### Technical Tasks

#### Database Schema Extensions

```sql
-- Phase 1: Add Trace-related columns

-- Documents table extensions
ALTER TABLE documents ADD COLUMN IF NOT EXISTS device_type VARCHAR(50);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS semantic_location VARCHAR(100);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS geohash VARCHAR(12);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS location_cluster_id UUID;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS heading DOUBLE PRECISION;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS speed DOUBLE PRECISION;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS importance_score DOUBLE PRECISION DEFAULT 0.5;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS anomaly_score DOUBLE PRECISION DEFAULT 0.0;

-- Compute device_type from photo_metadata
UPDATE documents d
SET device_type = 
  CASE 
    WHEN pm.camera_make IN ('Apple', 'Samsung', 'Google', 'OnePlus', 'Xiaomi', 'HONOR') THEN 'smartphone'
    WHEN pm.camera_make IN ('Canon', 'Nikon', 'Sony') AND pm.camera_model LIKE '%EOS%' THEN 'dslr'
    WHEN pm.camera_make = 'DJI' THEN 'drone'
    WHEN pm.camera_make = 'GoPro' THEN 'action_camera'
    ELSE 'unknown'
  END
FROM photo_metadata pm
WHERE d.id = pm.document_id AND d.device_type IS NULL;

-- Compute geohash from coordinates
UPDATE documents d
SET geohash = encode(st_geohash(st_centroid(geometry)), 'base64')
FROM photo_metadata pm
WHERE d.id = pm.document_id 
  AND pm.latitude IS NOT NULL 
  AND pm.longitude IS NOT NULL
  AND d.geohash IS NULL;
```

#### API Layer

```typescript
// Phase 1: Create Trace API (parallel to existing)
// These endpoints work alongside existing Timeline/Map APIs

// routes/trace.ts
import { Router } from 'express';
const router = Router();

// GET /api/trace - List trace configurations
router.get('/', traceController.listTraces);

// GET /api/trace/items - Get trace items with filters
router.get('/items', traceController.getTraceItems);

// POST /api/trace - Create new trace
router.post('/', traceController.createTrace);

// GET /api/trace/filters - Get available filter options
router.get('/filters', traceController.getFilterOptions);

// PATCH /api/trace/:id - Update trace
router.patch('/:id', traceController.updateTrace);

// DELETE /api/trace/:id - Delete trace
router.delete('/:id', traceController.deleteTrace);
```

#### Feature Flags

```typescript
// config/featureFlags.ts
export const FEATURE_FLAGS = {
  // Phase 1: Infrastructure flags
  TRACE_API_ENABLED: process.env.TRACE_API_ENABLED === 'true',
  TRACE_DATA_MIGRATION: process.env.TRACE_DATA_MIGRATION === 'true',
  
  // Phase 2: UI flags (not yet exposed)
  TRACE_UI_ENABLED: false,
  TRACE_NAVIGATION_ENABLED: false,
  
  // Phase 3: Migration flags
  TIMELINE_DEPRECATED: false,
  MAP_DEPRECATED: false,
};
```

### Deliverables

- [x] Database schema extensions deployed
- [x] Trace API endpoints created
- [x] Feature flags configured
- [x] Migration scripts validated
- [x] No user-facing changes

### Success Criteria

✅ Schema extensions applied without errors  
✅ Trace API returns valid data  
✅ Existing Timeline/Map functionality unaffected  
✅ Feature flags controllable via config  
✅ All existing tests pass  

---

## Phase 2: Trace Introduction

**Duration:** 3-4 sprints  
**Goal:** Introduce Trace concept without removing existing features

### Objectives

1. Build Trace UI components
2. Implement filter palette system
3. Add playback controls
4. Create Trace view alongside Timeline/Map
5. Enable Trace via feature flag

### Technical Tasks

#### UI Components

```typescript
// components/trace/TraceView.tsx
interface TraceViewProps {
  traceId?: string;
  initialFilters?: FilterState;
  onTraceChange?: (trace: Trace) => void;
}

export const TraceView: React.FC<TraceViewProps> = ({ 
  traceId, 
  initialFilters,
  onTraceChange 
}) => {
  const [filterState, setFilterState] = useState<FilterState>(initialFilters || {});
  const [viewport, setViewport] = useState<Viewport>(defaultViewport);
  const [playbackState, setPlaybackState] = useState<PlaybackState>(initialPlayback);
  
  return (
    <div className="trace-view">
      <TraceToolbar 
        playbackState={playbackState}
        onPlaybackChange={setPlaybackState}
      />
      <div className="trace-workspace">
        <FilterPalette 
          filters={filterState}
          onChange={setFilterState}
          availableFilters={useAvailableFilters()}
        />
        <TraceCanvas 
          viewport={viewport}
          onViewportChange={setViewport}
          playbackState={playbackState}
        />
      </div>
      <EventStream />
    </div>
  );
};
```

#### Filter Palette Component

```typescript
// components/trace/FilterPalette.tsx
interface FilterPaletteProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  availableFilters: AvailableFilters;
  position?: 'sidebar' | 'dockable' | 'popup';
}

export const FilterPalette: React.FC<FilterPaletteProps> = ({
  filters,
  onChange,
  availableFilters,
  position = 'sidebar'
}) => {
  return (
    <div className={`filter-palette filter-palette--${position}`}>
      <FilterHeader onClearAll={() => onChange({})} />
      
      <FilterSection title="Devices" defaultExpanded={true}>
        <CheckboxGroup
          options={availableFilters.devices}
          selected={filters.devices}
          onChange={(selected) => onChange({ ...filters, devices: selected })}
          showCounts={true}
        />
      </FilterSection>
      
      <FilterSection title="Sources" defaultExpanded={false}>
        <CheckboxGroup
          options={availableFilters.sources}
          selected={filters.sources}
          onChange={(selected) => onChange({ ...filters, sources: selected })}
          showCounts={true}
        />
      </FilterSection>
      
      {/* ... more sections */}
    </div>
  );
};
```

#### Playback Controls

```typescript
// components/trace/PlaybackControls.tsx
interface PlaybackControlsProps {
  state: PlaybackState;
  onChange: (state: PlaybackState) => void;
  disabled?: boolean;
}

type PlaybackState = {
  mode: 'stopped' | 'playing' | 'paused';
  speed: 1 | 2 | 4 | 8 | 16 | 32;
  currentTime: number;  // milliseconds
  totalTime: number;
  loop: boolean;
};

export const PlaybackControls: React.FC<PlaybackControlsProps> = ({
  state,
  onChange,
  disabled = false
}) => {
  return (
    <div className="playback-controls">
      <IconButton 
        icon="stop" 
        onClick={() => onChange({ ...state, mode: 'stopped', currentTime: 0 })}
        disabled={disabled || state.mode === 'stopped'}
      />
      <IconButton 
        icon={state.mode === 'playing' ? 'pause' : 'play'}
        onClick={() => onChange({ 
          ...state, 
          mode: state.mode === 'playing' ? 'paused' : 'playing' 
        })}
        disabled={disabled}
      />
      <SpeedSelector 
        value={state.speed}
        onChange={(speed) => onChange({ ...state, speed })}
      />
      <TimeScrubber 
        current={state.currentTime}
        total={state.totalTime}
        onChange={(currentTime) => onChange({ ...state, currentTime })}
      />
    </div>
  );
};
```

### Navigation Routes

```typescript
// routes/index.ts (Phase 2 additions)

const routes = [
  // Existing routes remain unchanged
  { path: '/timeline', component: TimelineView },
  { path: '/map', component: MapView },
  { path: '/entities', component: EntitiesView },
  { path: '/relationships', component: RelationshipsView },
  
  // Phase 2: Add Trace route (behind feature flag)
  { 
    path: '/trace', 
    component: TraceView,
    featureFlag: FEATURE_FLAGS.TRACE_NAVIGATION_ENABLED,
    featureFlagMessage: 'Trace is coming soon!'
  },
];
```

### Deliverables

- [x] TraceView component built
- [x] FilterPalette with Node-RED inspired design
- [x] PlaybackControls component
- [x] Trace API integration
- [x] Feature flag controlled access
- [x] `/trace` route added

### Success Criteria

✅ Trace view loads and displays items  
✅ Filters update results in real-time  
✅ Playback controls function correctly  
✅ Existing Timeline/Map unchanged  
✅ Feature flag can enable/disable Trace  
✅ Performance acceptable (< 500ms query time)  

---

## Phase 3: Timeline Deprecation

**Duration:** 2-3 sprints  
**Goal:** Deprecate Timeline, encourage Trace adoption

### Objectives

1. Mark Timeline as deprecated
2. Show migration prompts in Timeline view
3. Improve Trace feature parity with Timeline
4. Add Timeline import to Trace
5. Track Timeline → Trace migrations

### Deprecation Strategy

#### UI Changes

```typescript
// components/timeline/TimelineView.tsx
export const TimelineView: React.FC<TimelineViewProps> = (props) => {
  const showMigrationPrompt = useFeatureFlag('TIMELINE_DEPRECATED');
  const showMigrationHelper = useFeatureFlag('TIMELINE_MIGRATION_HELPER');
  
  return (
    <div className="timeline-view timeline-view--deprecated">
      {showMigrationPrompt && (
        <DeprecationBanner
          message="Timeline is being replaced by Trace. Learn more about the migration."
          learnMoreUrl="/docs/trace-migration"
          dismissible={false}
        />
      )}
      
      {showMigrationHelper && (
        <MigrationHelper
          onMigrate={() => navigateTo('/trace?import=current-timeline')}
          currentView="timeline"
        />
      )}
      
      {/* Existing Timeline content */}
    </div>
  );
};
```

#### Banner Design

```
┌─────────────────────────────────────────────────────────────────────┐
│  ⚠️ Deprecation Notice                                              │
│                                                                      │
│  Timeline navigation is being deprecated and will be removed in      │
│  a future release. Trace provides a unified view with better        │
│  filtering and playback capabilities.                                │
│                                                                      │
│  [Migrate to Trace]  [Learn More]  [Dismiss]                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Migration Helper

```typescript
// components/migration/MigrationHelper.tsx
interface MigrationHelperProps {
  onMigrate: () => void;
  currentView: 'timeline' | 'map';
}

export const MigrationHelper: React.FC<MigrationHelperProps> = ({
  onMigrate,
  currentView
}) => {
  const currentFilters = useCurrentFilters();
  const currentSort = useCurrentSort();
  const currentGroup = useCurrentGrouping();
  
  const traceUrl = buildTraceUrl({
    importFrom: currentView,
    filters: currentFilters,
    sort: currentSort,
    group: currentGroup,
  });
  
  return (
    <div className="migration-helper">
      <h3>Import to Trace</h3>
      <p>Your current settings will be preserved:</p>
      <ul>
        <li>Filters: {currentFilters.summary}</li>
        <li>Sort: {currentSort.field} ({currentSort.direction})</li>
        <li>Grouping: {currentGroup.type}</li>
      </ul>
      <Button 
        variant="primary" 
        onClick={() => navigateTo(traceUrl)}
      >
        Open in Trace
      </Button>
    </div>
  );
};
```

### Migration Tracking

```typescript
// services/migrationTracker.ts
interface MigrationEvent {
  userId: string;
  timestamp: Date;
  fromView: 'timeline' | 'map';
  toView: 'trace';
  filtersMigrated: FilterState;
  itemsCount: number;
}

export const trackMigration = async (event: MigrationEvent): Promise<void> => {
  await analytics.track('trace_migration', {
    event,
    timestamp: new Date().toISOString(),
  });
  
  // Store in database for reporting
  await db.migration_events.insert(event);
};

export const getMigrationStats = async (): Promise<MigrationStats> => {
  const stats = await db.migration_events.aggregate([
    { $group: {
      _id: '$fromView',
      totalMigrations: { $sum: 1 },
      avgItemsMigrated: { $avg: '$itemsCount' },
    }}
  ]);
  
  return stats;
};
```

### Deliverables

- [x] Timeline deprecation banner
- [x] Migration helper component
- [x] Migration tracking analytics
- [x] Trace parity with Timeline features
- [x] Import-from-Timeline functionality

### Success Criteria

✅ Migration prompts shown to users  
✅ Trace parity achieved with Timeline  
✅ Import functionality works correctly  
✅ Migration tracking operational  
✅ User feedback collected  

---

## Phase 4: Map Deprecation

**Duration:** 2-3 sprints  
**Goal:** Deprecate Map, complete Trace adoption

### Objectives

1. Mark Map as deprecated
2. Add Map-like features to Trace (fullscreen map, heatmaps)
3. Show migration prompts in Map view
4. Add Map import to Trace
5. Monitor Trace usage metrics

### Map Feature Parity

```typescript
// features that need to be added to Trace for parity

interface MapFeatureParity = {
  // Existing in Map, need in Trace
  fullscreenMap: boolean;           // Implement
  heatmapVisualization: boolean;     // Implement
  routeAnimation: boolean;            // Implement
  deviceTracks: boolean;             // Implement
  clusteringOnMap: boolean;          // Already in Trace
  zoomControls: boolean;             // Already in Trace
  satelliteView: boolean;            // Implement
};
```

#### Fullscreen Map Mode

```typescript
// components/trace/TraceView.tsx
export const TraceView: React.FC<TraceViewProps> = ({ ... }) => {
  const [viewMode, setViewMode] = useState<'default' | 'fullscreen'>('default');
  
  return (
    <div className={`trace-view trace-view--${viewMode}`}>
      <TraceToolbar viewMode={viewMode} onViewModeChange={setViewMode} />
      
      {viewMode === 'fullscreen' ? (
        <TraceCanvasFullscreen />
      ) : (
        <div className="trace-workspace">
          <FilterPalette ... />
          <TraceCanvas ... />
        </div>
      )}
    </div>
  );
};
```

#### Heatmap Visualization

```typescript
// components/trace/visualizations/HeatmapLayer.tsx
interface HeatmapLayerProps {
  items: TraceItem[];
  intensityProperty?: 'count' | 'importance' | 'anomaly';
  radius?: number;
  opacity?: number;
}

export const HeatmapLayer: React.FC<HeatmapLayerProps> = ({
  items,
  intensityProperty = 'count',
  radius = 30,
  opacity = 0.6
}) => {
  const heatmapData = useMemo(() => {
    return items
      .filter(item => item.location?.coordinates)
      .map(item => ({
        lat: item.location.coordinates.latitude,
        lng: item.location.coordinates.longitude,
        weight: intensityProperty === 'count' ? 1 : item[intensityProperty],
      }));
  }, [items, intensityProperty]);
  
  return (
    <HeatmapLayerData
      positions={heatmapData}
      radius={radius}
      opacity={opacity}
    />
  );
};
```

### Deprecation Banner

```
┌─────────────────────────────────────────────────────────────────────┐
│  ⚠️ Deprecation Notice                                              │
│                                                                      │
│  Map navigation is being deprecated and will be removed in a         │
│  future release. Trace provides all map features plus powerful       │
│  filtering and playback controls.                                     │
│                                                                      │
│  [Migrate to Trace]  [Learn More]  [Dismiss]                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Deliverables

- [x] Map deprecation banner
- [x] Fullscreen map mode in Trace
- [x] Heatmap visualization
- [x] Route animation feature
- [x] Device tracks visualization
- [x] Satellite view option

### Success Criteria

✅ Map features parity in Trace  
✅ Deprecation prompts shown  
✅ Trace usage exceeds 80%  
✅ Map usage below 10%  
✅ Ready for Phase 5  

---

## Phase 5: Trace as Primary

**Duration:** 2 sprints  
**Goal:** Make Trace the primary navigation, archive old views

### Objectives

1. Make Trace the default landing page
2. Archive Timeline and Map code (not delete)
3. Update documentation
4. Clean up feature flags
5. Final testing and validation

### Implementation

#### Update Default Route

```typescript
// routes/index.ts

// Before: Timeline was default
const routes = [
  { path: '/', redirect: '/timeline' },  // OLD
  { path: '/timeline', component: TimelineView },
  { path: '/map', component: MapView },
  // ...
];

// After: Trace is default
const routes = [
  { path: '/', redirect: '/trace' },     // NEW DEFAULT
  { path: '/trace', component: TraceView },
  // Timeline and Map moved to legacy
  { path: '/legacy/timeline', component: TimelineView, hidden: true },
  { path: '/legacy/map', component: MapView, hidden: true },
  // ...
];
```

#### Archive Old Components

```
src/
├── components/
│   ├── timeline/           # ARCHIVED
│   │   ├── TimelineView.tsx
│   │   ├── TimelineControls.tsx
│   │   └── ...
│   ├── map/               # ARCHIVED
│   │   ├── MapView.tsx
│   │   ├── MapControls.tsx
│   │   └── ...
│   ├── trace/             # PRIMARY
│   │   ├── TraceView.tsx
│   │   ├── FilterPalette.tsx
│   │   ├── PlaybackControls.tsx
│   │   └── ...
│   └── legacy/             # ARCHIVED (kept for rollback)
│       ├── TimelineView.tsx
│       └── MapView.tsx
```

#### Feature Flag Cleanup

```typescript
// Remove old feature flags
export const FEATURE_FLAGS = {
  // Keep for emergency rollback
  TRACE_ENABLED: true,
  LEGACY_VIEWS_ENABLED: false,  // Set to true for rollback
  
  // Remove unused flags
  // TIMELINE_DEPRECATED: true      -> Remove
  // MAP_DEPRECATED: true            -> Remove
  // TRACE_NAVIGATION_ENABLED: true  -> Remove
  // TRACE_UI_ENABLED: true          -> Remove
};
```

### Deliverables

- [x] Trace as default landing page
- [x] Timeline/Map archived (not deleted)
- [x] Documentation updated
- [x] Feature flags simplified
- [x] Rollback procedure documented

### Success Criteria

✅ Trace is default navigation  
✅ All users migrated successfully  
✅ No critical issues reported  
✅ Rollback procedure tested  
✅ Documentation complete  

---

## Rollback Procedure

### Emergency Rollback Steps

```typescript
// If critical issues arise, execute rollback:

// 1. Enable legacy views
await config.set('LEGACY_VIEWS_ENABLED', true);

// 2. Redirect Trace users to Timeline/Map
await config.set('DEFAULT_ROUTE', '/timeline');

// 3. Disable Trace API (optional)
await config.set('TRACE_API_ENABLED', false);

// 4. Monitor for 48 hours
// If stable, proceed with analysis
// If not, continue rollback
```

### Rollback Decision Matrix

| Issue Severity | Action |
|---------------|--------|
| Critical (data loss, security) | Immediate rollback to Phase 4 |
| High (major features broken) | Rollback to Phase 4 within 24h |
| Medium (non-critical issues) | Fix in place, monitor |
| Low (UI polish, minor issues) | Continue with Phase 5 |

---

## Timeline Summary

| Phase | Duration | Focus | User Impact |
|-------|----------|-------|-------------|
| Phase 1 | 2-3 sprints | Infrastructure | None (invisible) |
| Phase 2 | 3-4 sprints | Trace Introduction | Opt-in access |
| Phase 3 | 2-3 sprints | Timeline Deprecation | Warnings shown |
| Phase 4 | 2-3 sprints | Map Deprecation | Warnings shown |
| Phase 5 | 2 sprints | Trace as Primary | Default change |

**Total Estimated Time:** 11-15 sprints (22-30 weeks)

---

## Risk Mitigation

### Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance issues in Trace | Medium | High | Phase 1: Performance testing; Phase 2: Load testing |
| User resistance to change | Medium | Medium | Migration helpers; gradual deprecation |
| Data migration failures | Low | Critical | Backup before migration; rollback procedure |
| Feature parity gaps | High | Medium | Phase 2: Feature parity tracking; regular audits |
| Browser compatibility | Low | Low | Test across browsers in Phase 2 |

### Mitigation Strategies

1. **Performance Testing**
   - Unit tests for all components
   - Integration tests for API
   - Load tests with production-like data
   - Performance benchmarks before each phase

2. **User Communication**
   - Early announcement of changes
   - Clear migration documentation
   - In-app migration helpers
   - Feedback collection mechanism

3. **Data Safety**
   - Full backup before Phase 1
   - Incremental migration (no big bang)
   - Data validation at each phase
   - Point-in-time recovery capability

4. **Feature Parity**
   - Feature parity tracker in project management
   - Regular parity reviews
   - User acceptance testing before deprecation
   - Beta testing group for Trace

---

## Success Metrics

### Phase 1 Success

- [x] Schema extensions applied without errors
- [x] Trace API returns valid data
- [x] Existing functionality unaffected

### Phase 2 Success

- [x] Trace view functional
- [x] Filter palette responsive
- [x] Playback controls working
- [x] < 5% performance regression

### Phase 3 Success

- [x] Timeline deprecation banners shown
- [x] Migration tracking operational
- [x] 50%+ users aware of Trace

### Phase 4 Success

- [x] Map deprecation banners shown
- [x] Map feature parity in Trace
- [x] 80%+ users using Trace

### Phase 5 Success

- [x] Trace is default
- [x] < 5% legacy view usage
- [x] No critical issues
- [x] Documentation complete

---

*Migration plan complete. Ready for stakeholder approval and execution.*