# Operation Plugin Foundation - Validation Report

**Date:** 2026-07-05  
**Branch:** operation-plugin-foundation  
**Status:** IMPLEMENTATION INCOMPLETE - RECOMMEND HUMAN REVIEW BEFORE MERGE

---

## Executive Summary

The Operation Plugin Foundation implementation introduces plugin identity and provenance tracking across the Librarian codebase. While the migration schema and plugin registry are correctly implemented, **critical regressions and incomplete implementations were discovered** that prevent the feature from functioning correctly.

**Key Finding:** The migration `011_plugin_foundation.sql` adds provenance columns to the database, but the backend storage code (`storage/postgres_backend.py`) was **not updated** to populate these columns. This creates a silent failure where:
- New columns remain NULL
- Multi-engine support will not work
- Provenance tracking is non-functional

---

## Tests Performed

### 1. Migration Validation Tests
```bash
pytest tests/test_migration_manager.py -v
```
**Result:** 3 FAILED, 35 PASSED

| Test | Status | Issue |
|------|--------|-------|
| `test_target_schema_version` | ❌ FAIL | Expected 9, got 10 (test is stale) |
| `test_split_preserves_migration_005_pattern` | ❌ FAIL | Semicolon count assertion is stale |
| `test_filesystem_is_source_of_truth` | ❌ FAIL | 007_job_orchestration.sql inserts job_prerequisites |

### 2. Plugin Registry Validation
**Verified:**
- ✓ Plugin definitions include namespace, type, engine, version
- ✓ Registry correctly identifies installed plugins
- ✓ Validation against handlers works
- ✓ API routes for plugin management exist

### 3. Worker Identity Validation
**Verified:**
- ✓ `PhotoMetadataExtractor` has all identity fields
- ❌ `ThumbnailGenerator` missing identity fields
- ❌ `ContentExtractor` missing identity fields
- ❌ `EntityExtractor` missing identity fields
- ❌ `EventExtractor` missing identity fields
- ❌ `LocationExtractor` missing identity fields
- ❌ `EmbeddingGenerator` missing identity fields

### 4. Provenance Tracking Validation
**Verified:**
- ✓ `BaseWorker.get_provenance()` method exists
- ✓ Returns plugin_name, engine_name, plugin_version, processed_at, artifact_hash
- ❌ Backend `save_photo_metadata()` NOT updated for provenance columns
- ❌ ON CONFLICT still uses old `(document_id)` constraint

### 5. API Response Validation
**Verified:**
- ❌ `PluginInfo` response model missing identity fields (namespace, engine, version)
- ✓ `get_plugin_info()` in registry returns identity fields

---

## Failures Discovered

### CRITICAL - Regression: Backend Not Updated for Provenance

**Location:** `storage/postgres_backend.py` - `save_photo_metadata()` method (lines 839-930)

**Issue:** The migration `011_plugin_foundation.sql` adds:
- New columns: `plugin_name`, `engine_name`, `plugin_version`, `processed_at`, `artifact_hash`
- New UNIQUE constraint: `(document_id, plugin_name, engine_name)` for multi-engine support

But the backend code still:
- Inserts into old columns: `extraction_method`, `extraction_version`, `extracted_at`
- Uses old UNIQUE constraint: `(document_id)`
- Does NOT pass provenance values

**Impact:**
- New columns will be NULL for all future inserts
- Multi-engine EXIF extraction will fail (constraint violation)
- Provenance tracking is completely non-functional
- Stale columns remain in INSERT statement

**Fix Required:** Update `save_photo_metadata()` to:
1. Add new columns to INSERT statement
2. Remove or deprecate old columns
3. Update ON CONFLICT to new multi-engine constraint
4. Accept provenance values from caller

---

### HIGH - Missing Identity Fields in Workers

**Affected Workers:**
- `ThumbnailGenerator`
- `ContentExtractor`
- `EntityExtractor`
- `EventExtractor`
- `LocationExtractor`
- `EmbeddingGenerator`

**Issue:** These workers inherit from `BaseWorker` but don't define class-level identity fields (`PLUGIN_NAME`, `ENGINE_NAME`, `PLUGIN_VERSION`).

**Impact:**
- `get_provenance()` returns 'unknown' for these workers
- Cannot track which engine produced observations
- Violates plugin foundation principle

**Fix Required:** Add identity fields to each worker class.

---

### MEDIUM - API Response Missing Identity Fields

**Location:** `api/routes/settings.py` - `PluginInfo` model

**Issue:** The API response model doesn't include identity fields (`namespace`, `engine`, `version`).

**Impact:**
- API consumers cannot get complete plugin information
- Inconsistent with `registry.get_plugin_info()` which includes these fields

**Fix Required:** Add identity fields to `PluginInfo` model.

---

### LOW - Stale Test Assertions

| Test | Issue |
|------|-------|
| `test_target_schema_version` | Test expects 9, code correctly has 10 |
| `test_split_preserves_migration_005_pattern` | Semicolon count assertion is stale (migration unchanged) |
| `test_filesystem_is_source_of_truth` | False positive - 007_job_orchestration.sql seeds job prerequisites (not user data) |

---

## Fixes Applied (During Validation)

None - fixes require code changes beyond validation scope.

---

## Remaining Risks

### 1. Multi-Engine NULL Constraint Collision
The migration 011 changes the UNIQUE constraint from `(document_id)` to `(document_id, plugin_name, engine_name)`. Existing rows will have NULL values for the new columns.

**Risk Level:** HIGH

**Issue:** PostgreSQL treats NULL as distinct, so multiple rows with NULL plugin_name/engine_name would be allowed. However, if existing data has exactly one row per document (enforced by old constraint), adding the new constraint is safe.

**Concern:** If a document currently has multiple photo_metadata rows (unlikely but possible), the migration will fail.

### 2. Backend/Schema Contract Mismatch
The backend code uses old column names (`extraction_method`, `extraction_version`, `extracted_at`) but the schema now expects new names (`plugin_name`, `engine_name`, `plugin_version`, `processed_at`, `artifact_hash`).

**Risk Level:** HIGH

**Issue:** Even if the migration succeeds, the backend INSERT will fail because:
- It tries to insert into columns that may have been renamed/dropped
- The old `ON CONFLICT (document_id)` constraint no longer exists

**Recommendation:** Backend must be updated to match new schema.

### 3. Incomplete Multi-Engine Support
Even if backend is fixed, the job scheduling logic doesn't support multi-engine job types yet.

**Risk Level:** MEDIUM

**Recommendation:** Document that multi-engine is schema-ready but not yet wired up.

### 4. No Reprocessing Validation
No tests validate that reprocessing an artifact updates provenance correctly.

**Risk Level:** MEDIUM

**Recommendation:** Add integration test for reprocessing with provenance verification.

---

## Manual Validation Recommendations

1. **Database Migration Testing**
   - Test migration 011 on fresh database
   - Test migration 011 on database with existing photo_metadata records
   - Verify constraint change works correctly

2. **Backend Provenance Integration**
   - Verify `PhotoMetadataExtractor.process()` calls `get_provenance()`
   - Verify provenance dict is passed to `save_photo_metadata()`
   - Verify multi-engine INSERT/UPDATE works

3. **API Contract Verification**
   - Call GET /api/v1/settings/plugins
   - Verify response includes namespace, engine, version fields
   - Verify GET /api/v1/settings/plugins/{name} returns same fields

4. **Worker Identity Verification**
   - Run each worker with a test job
   - Verify observations have correct provenance in database

5. **Regression Testing**
   - Run full test suite after backend fix
   - Verify existing photo_metadata functionality unchanged

---

## Summary by Validation Area

| Area | Status | Notes |
|------|--------|-------|
| Migration Validation | ⚠️ PARTIAL | Schema correct, test assertions stale |
| Regression Validation | ❌ FAIL | Backend not updated, multi-engine broken |
| Provenance Validation | ❌ FAIL | Backend save methods not updated |
| Multi-Engine Readiness | ❌ FAIL | Schema ready, code not wired up |
| Reprocessing Validation | ⚠️ UNTESTED | No tests exist |
| Startup Validation | ✓ PASS | P15 validation works, worker starts |

---

## Next Steps (Human Decision Required)

1. **Critical Path (Must Fix Before Merge)**
   - Update `storage/postgres_backend.py::save_photo_metadata()` to use new provenance columns
   - Add identity fields to 6 missing workers
   - Update migration to handle existing data safely

2. **Post-Merge (Should Fix Soon)**
   - Update `api/routes/settings.py::PluginInfo` model
   - Fix stale test assertions
   - Add reprocessing validation tests

3. **Documentation (Nice to Have)**
   - Document multi-engine architecture
   - Document provenance field meanings
   - Update CHANGELOG.md for migration 011