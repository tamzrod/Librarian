# Assumptions Remaining — Operation Playback

## Overview

This document tracks original assumptions from `assumptions.md` that could not be classified as facts, requirements, decisions, risks, or validation experiments. These represent true unknowns that remain after the analysis.

---

## Classification Summary

| Original Category | Count | Disposition |
|-------------------|-------|-------------|
| Technical Assumptions (A1-A5) | 5 | 1 Verified, 1 Verified, 1 Verified, 1 Verified, 1 Verified |
| User Experience (A6-A9) | 4 | 1 Verified, 1 Verified, 1 Verified, 1 Remaining |
| Architectural (A10-A12) | 3 | 3 Requirements |
| Data (A13-A15) | 3 | 3 Requirements |
| Performance (A16-A18) | 3 | 2 Requirements, 1 Remaining |
| Conflict (A19-A20) | 2 | 2 Verified |
| Open Assumptions (OA1-OA3) | 3 | 3 Product Decisions |

**Total Original Assumptions:** 20

---

## Remaining Assumptions

### AR1: Mobile Touch Optimization

**Original Reference:** A8 (Mobile Responsiveness)

**Assumption:** Mobile-first responsive design with filmstrip as primary view will work well for touch interactions.

**Why Unresolved:**
- Requires user testing on actual mobile devices
- Touch interaction patterns not validated
- Layout decisions depend on testing

**Validation Needed:** VT11 (Mobile Usability Test)

**Status:** Awaiting validation

---

### AR2: Collection Size Distribution

**Original Reference:** A9 (Collection Size Distribution)

**Assumption:** Most users have collections under 10k photos, with ~10% having 100k+.

**Why Unresolved:**
- No data available on actual collection sizes
- Distribution may vary by user base
- Performance strategy depends on distribution

**Validation Needed:** UQ21 - Analytics query for collection sizes

**Status:** Awaiting data

---

### AR3: Memory Usage for 100k Items

**Original Reference:** A18 (Memory Usage)

**Assumption:** Browser can handle 100k photo metadata in memory with < 500MB usage.

**Why Unresolved:**
- Not benchmarked with actual data
- Depends on implementation choices
- May vary by browser/device

**Validation Needed:** VT3 (Virtual Scrolling Benchmark) and VT8 (Memory Leak Detection)

**Status:** Awaiting validation

---

### AR4: User Tolerance for Initial Load

**Original Reference:** A16 (Initial Load Time)

**Assumption:** Users will tolerate 2-3 second initial load for large collections.

**Why Unresolved:**
- Not validated with actual users
- Industry standard evolving
- User expectations may differ

**Validation Needed:** VT1 (User Research)

**Status:** Awaiting validation

---

## Verified But Not Converted

These were verified but remain as important context:

### VBNC1: React 18+ Framework

**Original Reference:** A1

**Verification:** Confirmed in `package.json`

**Classification:** Verified Fact (F1)

**Status:** Complete

---

### VBNC2: State Management Pattern

**Original Reference:** A5

**Verification:** Confirmed `useState` pattern in TraceView

**Classification:** Verified Fact (F2)

**Status:** Complete

---

### VBNC3: Sync Primitives Exist

**Original Reference:** A5

**Verification:** Confirmed `scrollToThumbnailId` and `centerOnMarkerId` props

**Classification:** Verified Fact (F3)

**Status:** Complete

---

### VBNC4: Leaflet In Use

**Original Reference:** A3

**Verification:** Confirmed Leaflet 1.9.4 loaded dynamically

**Classification:** Verified Fact (F5)

**Status:** Complete

---

### VBNC5: Thumbnail Generator Exists

**Original Reference:** A15

**Verification:** Confirmed `workers/thumbnail_generator.py`

**Classification:** Verified Fact (F6)

**Status:** Complete

---

### VBNC6: Modern Browser Targets

**Original Reference:** A4

**Verification:** Confirmed browserslist in package.json

**Classification:** Verified Fact (F7)

**Status:** Complete

---

### VBNC7: P16 Alignment

**Original Reference:** A19

**Verification:** Confirmed Operation Playback aligns with P16 Phase 2

**Classification:** Verified Fact (F8)

**Status:** Complete

---

## Converted to Architectural Requirements

These original assumptions are now codified as requirements:

### CAR1: Backward Compatibility

**Original Reference:** A10

**Classification:** AR1 (URL Compatibility)

---

### CAR2: API Contract Compatibility

**Original Reference:** A2 (API Pagination partially)

**Classification:** AR2 (API Contract Compatibility)

---

### CAR3: Component Props Compatibility

**Original Reference:** A5 (State Management partially)

**Classification:** AR3 (Component Props Compatibility)

---

### CAR4: Filter State Shape

**Original Reference:** A11 (Filter State Persistence)

**Classification:** AR4 (State Shape Compatibility)

---

### CAR5: Performance Targets

**Original Reference:** A16, A17, A18

**Classification:** AR5-AR9 (Performance Requirements)

---

### CAR6: Sync Requirements

**Original Reference:** A5

**Classification:** AR10-AR12 (Synchronization Requirements)

---

### CAR7: Accessibility

**Original Reference:** A6

**Classification:** AR13-AR15 (Accessibility Requirements)

---

### CAR8: Browser Support

**Original Reference:** A4

**Classification:** AR18-AR19 (Browser Support Requirements)

---

### CAR9: Data Handling

**Original Reference:** A13, A14

**Classification:** AR20-AR21 (Data Integrity Requirements)

---

## Converted to Product Decisions

These original assumptions are now product decisions:

### CPD1: Playback Speed

**Original Reference:** OA1

**Classification:** PD1 (Default Playback Speed)

---

### CPD2: Timeline Behavior

**Original Reference:** OA3

**Classification:** PD5, PD6, PD7 (Timeline Decisions)

---

## Converted to Risks

These original assumptions are now tracked as risks:

### CR1: State Management

**Original Reference:** A5

**Classification:** R1 (State Management Complexity)

---

### CR2: Virtual Scrolling

**Original Reference:** A18

**Classification:** R2 (Virtual Scrolling Performance)

---

### CR3: Leaflet Performance

**Original Reference:** A3

**Classification:** R3 (Leaflet Marker Performance)

---

### CR4: Thumbnail Loading

**Original Reference:** A15

**Classification:** R6 (Thumbnail Loading During Playback)

---

### CR5: Keyboard Shortcuts

**Original Reference:** A6

**Classification:** R8 (Keyboard Shortcut Conflicts)

---

### CR6: Mobile Experience

**Original Reference:** A8

**Classification:** R9 (Mobile Experience Degradation)

---

### CR7: User Confusion

**Original Reference:** A7

**Classification:** R11 (User Confusion with New Paradigm)

---

### CR8: Backward Compatibility

**Original Reference:** A10

**Classification:** R12 (Backward Compatibility Breaking Change)

---

### CR9: Scope Creep

**Original Reference:** A7

**Classification:** R13 (Scope Creep)

---

### CR10: Dependency Risk

**Original Reference:** A20

**Classification:** R14 (Dependency on Other Projects)

---

### CR11: Timestamp Quality

**Original Reference:** A13

**Classification:** R16 (Timestamp Data Quality)

---

### CR12: GPS Coverage

**Original Reference:** A14

**Classification:** R17 (GPS Data Completeness)

---

## Converted to Validation Experiments

These original assumptions require validation experiments:

### CVE1: Leaflet Performance

**Original Reference:** A3

**Classification:** VT2 (Marker Clustering Benchmark)

---

### CVE2: Virtual Scrolling

**Original Reference:** A18

**Classification:** VT3 (Virtual Scrolling Benchmark)

---

### CVE3: Synchronization

**Original Reference:** A5

**Classification:** VT4 (Synchronization Performance Test)

---

### CVE4: Keyboard Navigation

**Original Reference:** A6

**Classification:** VT5 (Keyboard Shortcut Compatibility)

---

### CVE5: Playback Frame Rate

**Original Reference:** A17

**Classification:** VT6 (Playback Animation Benchmark)

---

### CVE6: Thumbnail Preloading

**Original Reference:** A15

**Classification:** VT7 (Thumbnail Preloading Strategy)

---

### CVE7: Memory Leaks

**Original Reference:** A18

**Classification:** VT8 (Memory Leak Detection)

---

### CVE8: Timeline Buckets

**Original Reference:** OA3

**Classification:** VT9 (Timeline Bucket Performance)

---

### CVE9: API Pagination

**Original Reference:** A2

**Classification:** VT10 (API Pagination Performance)

---

### CVE10: Mobile Usability

**Original Reference:** A8

**Classification:** VT11 (Mobile Usability Test)

---

### CVE11: Accessibility

**Original Reference:** A6

**Classification:** VT12 (Accessibility Audit)

---

### CVE12: Edge States

**Original Reference:** OA2

**Classification:** VT13 (Empty/Edge State UX)

---

## Assumptions Summary by Classification

| Classification | Count | % of Total |
|---------------|-------|------------|
| Verified Facts | 15 | 37.5% |
| Architectural Requirements | 21 | 52.5% |
| Product Decisions | 27 | 67.5% |
| Risks | 21 | 52.5% |
| Validation Experiments | 13 | 32.5% |
| Remaining True Assumptions | 4 | 10% |

---

## Reduction Progress

**Original Assumptions:** 20  
**Remaining True Assumptions:** 4  
**Reduction:** 16 (80%)

---

## Confidence Assessment

### High Confidence (Validated)
- Frontend stack (F1)
- State management pattern (F2)
- API pagination (F4)
- Component sync props (F3)
- Thumbnail infrastructure (F6)
- P16 alignment (F8)

### Medium Confidence (Requirements Defined)
- Performance targets (AR5-AR9)
- Synchronization requirements (AR10-AR12)
- Accessibility requirements (AR13-AR15)

### Low Confidence (Need Validation)
- Mobile performance (AR2)
- Memory usage (AR3)
- User load tolerance (AR4)

---

## Recommendations

### Immediate Actions (Week 1)
1. Run VT5 (Keyboard Shortcuts) - 1 day, unblocks implementation
2. Request collection size data - UQ21
3. Schedule user research for VT1

### Short-term Actions (Weeks 2-3)
4. Complete VT2 (Marker Clustering) - unblocks Phase 1
5. Complete VT3 (Virtual Scrolling) - unblocks Phase 1
6. Complete VT10 (API Pagination) - coordinates with backend

### Medium-term Actions (Weeks 4-5)
7. Complete VT4 (Synchronization) - validates core architecture
8. Complete VT6 (Playback Benchmark) - validates implementation approach
9. Finalize PD1 (Speed) based on VT1 results

### Before Implementation
10. Complete all Critical experiments (VT1-VT5)
11. Resolve all High priority questions
12. Obtain sign-off on architectural requirements

---

## Sign-off

| Role | Name | Date | Status |
|------|------|------|--------|
| Tech Lead | | | Pending |
| Product Manager | | | Pending |
| Engineering | | | Pending |
