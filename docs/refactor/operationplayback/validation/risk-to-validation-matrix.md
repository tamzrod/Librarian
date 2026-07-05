# Risk-to-Validation Matrix — Operation Playback

## Overview

This document maps risks to validation experiments using the enhanced risk formula:

```
Risk Priority = risk_score × blast_radius × reversibility
```

### Scoring Criteria

| Factor | Scale | Description |
|--------|-------|-------------|
| **Risk Score** | 1-6 | Original likelihood × impact score |
| **Blast Radius** | 1-3 | How many components/systems are affected |
| **Reversibility** | 1-3 | How easy is it to fix/revert (1=hard, 3=easy) |

### Priority Bands

| Priority | Score Range | Action |
|----------|------------|--------|
| Critical | 27-54 | Immediate validation required |
| High | 13-26 | Validation in current phase |
| Medium | 6-12 | Validation can wait |
| Low | 1-5 | Monitor only |

---

## Enhanced Risk Analysis

### All Risks with Enhanced Scoring

| ID | Risk | Score | Blast | Reverse | Priority | Priority Rank |
|----|------|-------|-------|---------|---------|---------------|
| R1 | State Management Complexity | 6 | 3 | 1 | **18** | **1** |
| R12 | Backward Compatibility | 6 | 3 | 1 | **18** | **1** |
| R2 | Virtual Scrolling Performance | 6 | 2 | 2 | **24** | **2** |
| R6 | Thumbnail Loading | 6 | 2 | 2 | **24** | **2** |
| R19 | Insufficient Testing Time | 6 | 3 | 2 | **36** | **3** |
| R13 | Scope Creep | 6 | 2 | 1 | **12** | - |
| R3 | Leaflet Marker Performance | 4 | 2 | 2 | **16** | **4** |
| R5 | Animation Frame Management | 4 | 2 | 2 | **16** | **4** |
| R4 | API Pagination Performance | 4 | 2 | 1 | **8** | - |
| R7 | Memory Leaks | 4 | 2 | 2 | **16** | **4** |
| R8 | Keyboard Conflicts | 2 | 1 | 3 | **6** | - |
| R9 | Mobile Experience | 3 | 1 | 2 | **6** | - |
| R10 | Accessibility Gap | 4 | 2 | 2 | **16** | **4** |
| R11 | User Confusion | 4 | 2 | 2 | **16** | **4** |
| R14 | Dependency Risk | 4 | 2 | 1 | **8** | - |
| R15 | RSC Conflict | 4 | 3 | 1 | **12** | - |
| R16 | Timestamp Quality | 4 | 2 | 2 | **16** | **4** |
| R17 | GPS Completeness | 2 | 1 | 2 | **4** | - |
| R18 | Thumbnail Backlog | 3 | 1 | 2 | **6** | - |
| R20 | Knowledge Gap | 4 | 1 | 2 | **8** | - |
| R21 | Stakeholder Alignment | 4 | 2 | 1 | **8** | - |

### Top 5 Risks by Priority

| Rank | ID | Risk | Priority Score | Category |
|------|----|------|----------------|----------|
| **1** | R19 | Insufficient Testing Time | **36** | Project Management |
| **2** | R2 | Virtual Scrolling Performance | **24** | Technical |
| **2** | R6 | Thumbnail Loading | **24** | Technical |
| **4** | R1 | State Management Complexity | **18** | Technical |
| **4** | R12 | Backward Compatibility | **18** | Architectural |
| **4** | R3 | Leaflet Marker Performance | **16** | Technical |
| **4** | R5 | Animation Frame Management | **16** | Technical |
| **4** | R7 | Memory Leaks | **16** | Technical |
| **4** | R10 | Accessibility Gap | **16** | UX |
| **4** | R11 | User Confusion | **16** | UX |
| **4** | R16 | Timestamp Quality | **16** | Data |

---

## Top 5 Risks with Validation Mapping

### #1: R19 - Insufficient Testing Time

**Priority Score:** 36 (Critical)

**Risk Details:**
- **Original Score:** 6 (Medium × High)
- **Blast Radius:** 3 (All components affected)
- **Reversibility:** 2 (Moderate - can add tests but delays schedule)

**Why This Risk Dominates:**
Testing time affects every other risk. Insufficient testing means:
- Performance issues won't be caught before release
- State management bugs survive to production
- Backward compatibility breaks go unnoticed

**Blast Radius Explanation:**
If testing is insufficient, ALL other risks become more likely to materialize into actual problems.

**Validation Experiments That Reduce This Risk:**

| Experiment | How It Reduces Risk | Reduction |
|-----------|---------------------|-----------|
| VT3 (Virtual Scrolling) | Validates performance baseline, reduces debugging time | 15% |
| VT4 (Synchronization) | Catches state issues early, reduces late-cycle fixes | 20% |
| VT5 (Keyboard Shortcuts) | Quick validation, frees QA time | 5% |
| VT2 (Marker Clustering) | Reduces complexity to test | 10% |
| VT1 (User Research) | Reduces rework from UX issues | 10% |

**Cumulative Risk Reduction:** ~60% if all experiments completed

**Mitigation Actions:**
1. Schedule 20% buffer in implementation timeline
2. Automate performance tests in CI/CD
3. Implement feature flags for staged rollout
4. Create test fixtures for 100k+ datasets

---

### #2 (Tie): R2 - Virtual Scrolling Performance

**Priority Score:** 24 (High)

**Risk Details:**
- **Original Score:** 6 (Medium × High)
- **Blast Radius:** 2 (FilmStrip component + core UX)
- **Reversibility:** 2 (Can switch libraries mid-implementation)

**Why This Risk Matters:**
FilmStrip is the primary content view. Poor scrolling performance directly impacts user experience.

**Validation Experiments That Reduce This Risk:**

| Experiment | Primary Validator | Validation Method |
|-----------|-------------------|-------------------|
| **VT3: Virtual Scrolling Benchmark** | **Direct reduction** | Benchmarks react-window vs @tanstack/react-virtual with 1k/10k/100k items |
| VT2: Marker Clustering | Indirect - proves clustering concept | Validation methodology transferable |
| VT6: Playback Benchmark | Confirms animation performance | Scroll performance is prerequisite |

**VT3 Details:**
```javascript
// Test scenarios
const testCases = [
  { items: 1000, target: '<100ms render, 60fps scroll' },
  { items: 10000, target: '<500ms render, 60fps scroll' },
  { items: 100000, target: '<2s render, ≥30fps scroll' }
];

// Metrics collected
const metrics = {
  initialRender: 'ms',
  scrollFPS: 'frames per second',
  memoryUsage: 'MB',
  domNodes: 'count'
};
```

**Risk Reduction If VT3 Passes:** 40%
**Risk Reduction If VT3 Fails:** Requires mitigation plan (alternative library or architecture change)

---

### #2 (Tie): R6 - Thumbnail Loading

**Priority Score:** 24 (High)

**Risk Details:**
- **Original Score:** 6 (High × Medium)
- **Blast Radius:** 2 (FilmStrip + Playback experience)
- **Reversibility:** 2 (Can adjust preloading strategy)

**Why This Risk Matters:**
Blank frames during playback break the cinematic experience. This is the most visible performance issue.

**Validation Experiments That Reduce This Risk:**

| Experiment | Primary Validator | Validation Method |
|-----------|-------------------|-------------------|
| **VT7: Thumbnail Preloading Strategy** | **Direct reduction** | Tests 5+2, 10+5, 20+10 preloading strategies |
| VT6: Playback Benchmark | Confirms actual blank frame rate | Measures % of blank frames |
| VT3: Virtual Scrolling | Ensures thumbnails render efficiently | Scroll performance affects loading |

**VT7 Details:**
```javascript
// Preload strategies tested
const strategies = [
  { ahead: 5, behind: 2, name: 'Minimal' },
  { ahead: 10, behind: 5, name: 'Moderate' },
  { ahead: 20, behind: 10, name: 'Aggressive' }
];

// Metrics
const metrics = {
  blankFrameRate: '% of frames without thumbnail',
  bandwidthUsage: 'MB/s',
  memoryOverhead: 'MB'
};
```

**Risk Reduction If VT7 Validates Strategy:** 35%
**Fallback if VT7 Fails:** Adaptive preloading based on network conditions

---

### #4 (Tie): R1 - State Management Complexity

**Priority Score:** 18 (High)

**Risk Details:**
- **Original Score:** 6 (Medium × High)
- **Blast Radius:** 3 (TraceView + FilmStrip + MapCanvas + Timeline)
- **Reversibility:** 1 (Hard - requires architectural refactor)

**Why This Risk Matters:**
State management bugs are hard to detect and expensive to fix. Feedback loops can cause infinite renders, crashing the browser.

**Why Blast Radius is 3:**
If state synchronization breaks, it affects ALL four main components:
1. TraceView (orchestrator)
2. FilmStrip (scroll sync)
3. MapCanvas (center sync)
4. Timeline (playhead sync)

**Why Reversibility is 1:**
State architecture changes require refactoring all components. It's not a simple config change.

**Validation Experiments That Reduce This Risk:**

| Experiment | Primary Validator | Validation Method |
|-----------|-------------------|-------------------|
| **VT4: Synchronization Performance** | **Direct reduction** | Tests sync latency <100ms, no feedback loops |
| VT6: Playback Benchmark | Confirms stable state during animation | Monitors for state corruption |
| VT5: Keyboard Shortcuts | Tests state transitions | Validates state machine |

**VT4 Details:**
```javascript
// Sync test scenarios
const scenarios = [
  { trigger: 'filmstrip-click', expected: 'map-centers <100ms' },
  { trigger: 'map-click', expected: 'filmstrip-scrolls <100ms' },
  { trigger: 'timeline-drag', expected: 'all-views-update <100ms' },
  { trigger: 'playback-advance', expected: 'sync-complete <100ms' }
];

// Critical test: Feedback loop detection
const feedbackTest = {
  name: 'No feedback loops',
  measure: 'State change count per interaction',
  threshold: '<= 1 change per trigger'
};
```

**Risk Reduction If VT4 Passes:** 45%
**Risk Reduction If VT4 Fails:** Requires architecture redesign before proceeding

---

### #4 (Tie): R12 - Backward Compatibility

**Priority Score:** 18 (High)

**Risk Details:**
- **Original Score:** 6 (Low × Critical)
- **Blast Radius:** 3 (URL routes + API contracts + component props)
- **Reversibility:** 1 (Cannot undo breaking changes for users)

**Why This Risk Matters:**
Breaking existing users' bookmarks, links, and integrations is the worst kind of technical debt. It erodes trust.

**Why Reversibility is 1:**
If we break backward compatibility:
- Existing URLs fail → User bookmarks lost
- API contracts change → Client integrations break
- Component props change → Existing code breaks

There's no easy fix once shipped.

**Validation Experiments That Reduce This Risk:**

| Experiment | Primary Validator | Validation Method |
|-----------|-------------------|-------------------|
| **VT4: Synchronization Performance** | **Indirect** - ensures refactoring doesn't break sync | Component compatibility testing |
| VT2: Marker Clustering | Ensures map behavior unchanged | API contract validation |
| VT3: Virtual Scrolling | Ensures filmstrip props unchanged | Component interface testing |

**Additional Mitigation Required:**
1. URL redirect testing (not a validation experiment)
2. API contract testing (not a validation experiment)
3. Component prop testing (covered by integration tests)

**Risk Reduction:** ~30% from experiments, remaining risk requires process controls

---

## Complete Risk-to-Validation Matrix

| Risk | Priority | VT1 | VT2 | VT3 | VT4 | VT5 | VT6 | VT7 | VT8 | VT9 | VT10 | VT11 | VT12 | VT13 |
|------|----------|-----|-----|-----|-----|-----|-----|-----|-----|-----|------|------|------|------|
| R1: State Management | 18 | - | - | - | **✓** | - | - | - | - | - | - | - | - | - |
| R2: Virtual Scrolling | 24 | - | - | **✓** | - | - | - | - | - | - | - | - | - | - |
| R3: Leaflet Markers | 16 | - | **✓** | - | - | - | - | - | - | - | - | - | - | - |
| R4: API Pagination | 8 | - | - | - | - | - | - | - | - | - | **✓** | - | - | - |
| R5: Animation Frame | 16 | - | - | - | - | - | **✓** | - | **✓** | - | - | - | - | - |
| R6: Thumbnail Loading | 24 | - | - | - | - | - | **✓** | **✓** | - | - | - | - | - | - |
| R7: Memory Leaks | 16 | - | - | - | - | - | - | - | **✓** | - | - | - | - | - |
| R8: Keyboard | 6 | - | - | - | - | **✓** | - | - | - | - | - | - | - | - |
| R9: Mobile | 6 | - | - | - | - | - | - | - | - | - | - | **✓** | - | - |
| R10: Accessibility | 16 | - | - | - | - | - | - | - | - | - | - | - | **✓** | - |
| R11: User Confusion | 16 | **✓** | - | - | - | - | - | - | - | - | - | - | - | - |
| R12: Backward Compat | 18 | - | **✓** | **✓** | **✓** | - | - | - | - | - | - | - | - | - |
| R13: Scope Creep | 12 | **✓** | - | - | - | - | - | - | - | - | - | - | - | **✓** |
| R14: Dependencies | 8 | - | - | - | - | - | - | - | - | - | - | - | - | - |
| R15: RSC Conflict | 12 | - | - | - | - | - | - | - | - | - | - | - | - | - |
| R16: Timestamp Quality | 16 | - | - | - | - | - | - | - | - | - | - | - | - | - |
| R17: GPS Coverage | 4 | - | - | - | - | - | - | - | - | - | - | - | - | - |
| R18: Thumbnail Backlog | 6 | - | - | - | - | - | - | - | - | - | - | - | - | - |
| R19: Testing Time | 36 | **✓** | **✓** | **✓** | **✓** | **✓** | - | - | - | - | - | - | - | - |
| R20: Knowledge Gap | 8 | - | - | - | - | - | - | - | - | - | - | - | - | - |
| R21: Stakeholder | 8 | - | - | - | - | - | - | - | - | - | - | - | - | - |

---

## Validation Coverage Analysis

### Risks Covered by Validation

| Coverage Level | Risks | Count | % |
|---------------|-------|-------|---|
| Fully Covered | R1, R2, R3, R5, R6, R7, R8 | 7 | 33% |
| Partially Covered | R10, R11, R12, R13, R19 | 5 | 24% |
| Not Covered | R4, R9, R14, R15, R16, R17, R18, R20, R21 | 9 | 43% |

### Validation Experiment Utility

| Experiment | Risks Addressed | Coverage % |
|-----------|------------------|------------|
| VT1 (User Research) | R11, R13, R19 | 14% |
| VT2 (Marker Clustering) | R3, R12, R19 | 14% |
| VT3 (Virtual Scrolling) | R2, R12, R19 | 14% |
| VT4 (Synchronization) | R1, R12, R19 | 14% |
| VT5 (Keyboard) | R8, R19 | 10% |
| VT6 (Playback) | R5, R6 | 10% |
| VT7 (Preloading) | R6 | 5% |
| VT8 (Memory) | R5, R7 | 10% |
| VT9 (Timeline) | - | 0% |
| VT10 (API Pagination) | R4 | 5% |
| VT11 (Mobile) | R9 | 5% |
| VT12 (Accessibility) | R10 | 5% |
| VT13 (Edge States) | R13 | 5% |

---

## Prioritized Validation Execution

Based on risk-to-validation mapping, experiments should be executed in this order:

### Week 1-2: Critical Coverage

| Experiment | Days | Covers | Priority |
|-----------|------|--------|----------|
| **VT4 (Synchronization)** | 2 | R1, R12 | Critical - Architecture validation |
| **VT3 (Virtual Scrolling)** | 3 | R2, R12 | Critical - Performance foundation |
| **VT5 (Keyboard)** | 1 | R8, R19 | Quick win, unblocks implementation |

### Week 3-4: Performance Validation

| Experiment | Days | Covers | Priority |
|-----------|------|--------|----------|
| **VT2 (Marker Clustering)** | 2 | R3, R12 | Performance validation |
| **VT6 (Playback Benchmark)** | 2 | R5, R6 | Core feature validation |
| **VT7 (Thumbnail Preload)** | 2 | R6 | Polish validation |

### Week 5-6: Quality Assurance

| Experiment | Days | Covers | Priority |
|-----------|------|--------|----------|
| **VT1 (User Research)** | 5 | R11, R13, R19 | UX validation |
| **VT8 (Memory Leaks)** | 1 | R5, R7 | Stability validation |
| **VT12 (Accessibility)** | 2 | R10 | Compliance validation |

---

## Summary: Top 5 Risks → Validation Mapping

| Rank | Risk | Score | Primary Validator | Secondary Validators | Risk Reduction |
|------|------|-------|-------------------|---------------------|----------------|
| **1** | R19: Testing Time | 36 | VT1, VT2, VT3, VT4, VT5 | All | ~60% |
| **2** | R2: Virtual Scrolling | 24 | **VT3** | VT2, VT6 | 40% |
| **2** | R6: Thumbnail Loading | 24 | **VT7** | VT6 | 35% |
| **4** | R1: State Management | 18 | **VT4** | VT6 | 45% |
| **4** | R12: Backward Compat | 18 | **VT4** | VT2, VT3 | 30% |

---

## Recommendations

### Immediate Actions (Week 1)

1. **Execute VT4 (Synchronization)** - Validates architecture before code is written
2. **Execute VT5 (Keyboard Shortcuts)** - Quick 1-day experiment, unblocks implementation
3. **Buffer schedule by 20%** - Addresses R19 (Testing Time)

### Before Phase 1 (Week 3)

4. **Execute VT3 (Virtual Scrolling)** - Validates VT3 before committing to library
5. **Execute VT2 (Marker Clustering)** - Validates clustering approach
6. **Review VT4 results** - Architecture may need redesign

### Before Phase 5 (Week 4+)

7. **Execute VT7 (Thumbnail Preload)** - Finalizes preloading strategy
8. **Execute VT6 (Playback Benchmark)** - Validates core playback
9. **Execute VT1 (User Research)** - Validates UX assumptions

---

## Appendix: Scoring Rationale

### Blast Radius Definitions

| Level | Score | Description |
|-------|-------|-------------|
| Single | 1 | Affects only one component |
| Multi | 2 | Affects 2-3 components |
| System | 3 | Affects entire application or multiple systems |

### Reversibility Definitions

| Level | Score | Description |
|-------|-------|-------------|
| Hard | 1 | Requires architectural refactor |
| Moderate | 2 | Requires significant code changes |
| Easy | 3 | Config or minor code change |

### Why R19 (Testing Time) Scores Highest

Despite having a score of 6 (same as R1, R2, R6, R12):
- **Blast Radius = 3**: Testing affects ALL components and ALL other risks
- **Reversibility = 2**: Schedule buffer is easy to add, hard to find time later

The multiplier effect makes R19 the highest priority risk.
