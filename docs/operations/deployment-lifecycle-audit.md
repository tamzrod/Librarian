# Deployment Lifecycle Audit

**Document Type:** Architecture Review and Risk Analysis  
**Status:** Audit Complete - Awaiting Implementation Decisions  
**Date:** 2026-07-06

---

## Executive Summary

This document provides a comprehensive audit of Librarian's deployment scripts against the intended 3-tier reset model. The audit reveals that the current implementation has several inconsistencies, risks, and opportunities for improvement.

**Key Finding:** The scripts have been partially updated from a previous operation, but the implementation is incomplete and not fully aligned with the intended 3-tier lifecycle model.

---

## 1. Current Script Behavior Analysis

### 1.1 rebuild.sh

| Command | Behavior |
|---------|----------|
| `docker compose down` | Stops and removes containers. Volumes are NOT removed by default. |
| `docker compose build --no-cache` | Builds images without using Docker cache. |
| `docker compose up -d` | Starts containers in detached mode. |

**Data Preservation Status:**
- ✅ `/library` - Preserved (host-mounted read-only)
- ✅ PostgreSQL database - Preserved (postgres_data volume)
- ✅ `/librarian-data` - Preserved (librarian_data volume)
- ✅ `/plugin-dependencies` - Preserved (plugin_dependencies volume)
- ✅ `/plugin-cache` - Preserved (plugin_cache volume)

**Issues Identified:**
1. **No image pruning option** - Images are rebuilt but old ones remain as dangling
2. **Documentation mismatch** - The script header says "Force a clean rebuild" but doesn't clean images

### 1.2 reset.sh

| Command | Behavior |
|---------|----------|
| `docker compose down` | Stops and removes containers only |
| `docker volume rm` (explicit) | Removes specific named volumes |
| `docker system prune -f` | Removes stopped containers, unused networks, dangling images |
| `docker compose up -d --build` | Builds and starts containers |

**Current Implementation:**
```bash
# Explicit volume removal
docker volume rm librarian-postgres_data
docker volume rm librarian-librarian_data

# Conditional plugin volume removal
if [ "$PURGE_PLUGINS" = true ]; then
    docker volume rm librarian-plugin_dependencies
    docker volume rm librarian-plugin_cache
fi
```

**Data Preservation Status (default):**
- ✅ `/library` - Preserved (host-mounted)
- ✅ `/plugin-dependencies` - Preserved
- ✅ `/plugin-cache` - Preserved
- ❌ PostgreSQL database - DELETED
- ❌ `/librarian-data` - DELETED

**Data Preservation Status (--purge-plugins):**
- ✅ `/library` - Preserved (host-mounted)
- ❌ PostgreSQL database - DELETED
- ❌ `/librarian-data` - DELETED
- ❌ `/plugin-dependencies` - DELETED
- ❌ `/plugin-cache` - DELETED

**Issues Identified:**
1. **No nuclear option** - `--purge-plugins` is close but doesn't match the intended Level 3 model
2. **Missing --nuclear flag** - The intended Level 3 reset command doesn't exist
3. **No library data reset** - `/librarian-data` is reset but there's no option to preserve derived artifacts for re-indexing

### 1.3 update.sh

| Command | Behavior |
|---------|----------|
| `git pull` | Pulls latest code |
| `docker compose pull` | Pulls latest images |
| `docker compose down` | Stops and removes containers |
| `docker compose up -d --build` | Builds and starts containers |

**Data Preservation Status:**
- ✅ `/library` - Preserved (host-mounted)
- ✅ PostgreSQL database - Preserved (postgres_data volume)
- ✅ `/librarian-data` - Preserved (librarian_data volume)
- ✅ `/plugin-dependencies` - Preserved (plugin_dependencies volume)
- ✅ `/plugin-cache` - Preserved (plugin_cache volume)

**Issues Identified:**
1. **No issues** - This script correctly preserves all data

### 1.4 dev.sh

This is a dispatcher script that delegates to other scripts. No direct data impact.

### 1.5 status.sh

Read-only script. No data impact.

### 1.6 logs.sh

Read-only script. No data impact.

### 1.7 smoke_test.sh

| Command | Behavior |
|---------|----------|
| `docker compose up -d --build` | Builds and starts containers |

**Data Preservation Status:**
- ✅ All volumes preserved (uses `up` not `down`)

**Issues Identified:**
1. **Minor**: Running smoke tests could leave containers running if interrupted

---

## 2. Intended vs. Current Behavior Matrix

### Intended Level 1 — Rebuild

| Data | Intended | Current | Status |
|------|----------|---------|--------|
| `/library` | Preserve | Preserve | ✅ Match |
| PostgreSQL | Preserve | Preserve | ✅ Match |
| `/librarian-data` | Preserve | Preserve | ✅ Match |
| `/plugin-dependencies` | Preserve | Preserve | ✅ Match |
| `/plugin-cache` | Preserve | Preserve | ✅ Match |

### Intended Level 2 — Database Reset

| Data | Intended | Current | Status |
|------|----------|---------|--------|
| `/library` | Preserve | Preserve | ✅ Match |
| `/plugin-dependencies` | Preserve | Preserve | ✅ Match |
| `/plugin-cache` | Preserve | Preserve | ✅ Match |
| PostgreSQL | Destroy | Destroy | ✅ Match |
| `/librarian-data` | Destroy | Destroy | ✅ Match |

### Intended Level 3 — Nuclear Reset

| Data | Intended | Current | Status |
|------|----------|---------|--------|
| `/library` | Preserve | Preserve | ✅ Match |
| PostgreSQL | Destroy | Destroy | ✅ Match |
| `/librarian-data` | Destroy | Destroy | ✅ Match |
| `/plugin-dependencies` | Destroy | Destroy* | ⚠️ Partial |
| `/plugin-cache` | Destroy | Destroy* | ⚠️ Partial |
| Containers | Destroy | Destroy | ✅ Match |
| Images | Destroy | Preserved* | ❌ No match |
| Build cache | Destroy | Preserved* | ❌ No match |

*Note: The current `--purge-plugins` flag only removes plugin volumes, not images or build cache.

---

## 3. Docker Command Analysis

### 3.1 Command Reference

| Command | Effect | Used In |
|---------|--------|---------|
| `docker compose down` | Removes containers/networks, **preserves volumes** | rebuild.sh, update.sh, reset.sh |
| `docker compose down -v` | Removes containers/networks **AND volumes** | **Never used** (was in original reset.sh) |
| `docker volume rm <name>` | Removes specific named volume | reset.sh (explicit) |
| `docker system prune -f` | Removes stopped containers, unused networks, **dangling images** | reset.sh |
| `docker image prune -a` | Removes **all** unused images | **Never used** |
| `docker builder prune` | Removes build cache | **Never used** |

### 3.2 Consequences of Each Command

| Command | Containers | Volumes | Images | Networks | Build Cache |
|---------|------------|---------|--------|----------|-------------|
| `docker compose down` | ✅ Removed | ❌ Preserved | ❌ Preserved | ✅ Removed | ❌ Preserved |
| `docker compose down -v` | ✅ Removed | ✅ Removed | ❌ Preserved | ✅ Removed | ❌ Preserved |
| `docker volume rm <name>` | ❌ Unchanged | ✅ Removed | ❌ Unchanged | ❌ Unchanged | ❌ Unchanged |
| `docker system prune -f` | ✅ Removed | ❌ Unchanged | ⚠️ Dangling only | ✅ Removed | ❌ Unchanged |
| `docker image prune -a` | ❌ Unchanged | ❌ Unchanged | ✅ All unused | ❌ Unchanged | ❌ Unchanged |
| `docker builder prune` | ❌ Unchanged | ❌ Unchanged | ❌ Unchanged | ❌ Unchanged | ✅ Removed |

### 3.3 Volume Leakage Analysis

**Named Volumes (in compose file):**
- `postgres_data` - Managed by compose, survives `docker compose down`
- `librarian_data` - Managed by compose, survives `docker compose down`
- `plugin_dependencies` - Managed by compose, survives `docker compose down`
- `plugin_cache` - Managed by compose, survives `docker compose down`

**Host-Mounted Paths (NOT volumes):**
- `/library` - Host-mounted, never affected by Docker operations

**Key Finding:** The current implementation correctly uses explicit `docker volume rm` for targeted volume removal, avoiding the broad destruction of `docker compose down -v`.

---

## 4. Data Ownership Boundaries

### 4.1 Ownership Matrix

| Path | Owner | Type | Managed By |
|------|-------|------|------------|
| `/library` | User | Evidence | User (host filesystem) |
| `postgres_data` | Librarian | Catalog | Docker volumes |
| `/librarian-data` | Librarian | Artifacts | Docker volumes |
| `/plugin-dependencies` | Librarian | Infrastructure | Docker volumes |
| `/plugin-cache` | Librarian | Cache | Docker volumes |

### 4.2 Consistency Analysis

✅ **Consistent:** All scripts treat `/library` as user-owned (never deleted)  
✅ **Consistent:** All scripts treat PostgreSQL as reset-able  
✅ **Consistent:** All scripts treat `/librarian-data` as reset-able  
✅ **Consistent:** Plugin volumes are preserved in rebuild/update, conditional in reset  
⚠️ **Inconsistent:** No script allows selective preservation of `/librarian-data` during reset

---

## 5. Plugin Dependency Persistence Analysis

### 5.1 Current Behavior

| Operation | plugin_dependencies | plugin_cache |
|-----------|--------------------|--------------|
| `docker compose down` | ✅ Preserved | ✅ Preserved |
| `docker compose up` | ✅ Preserved | ✅ Preserved |
| `rebuild.sh` | ✅ Preserved | ✅ Preserved |
| `update.sh` | ✅ Preserved | ✅ Preserved |
| `reset.sh` (default) | ✅ Preserved | ✅ Preserved |
| `reset.sh --purge-plugins` | ❌ Deleted | ❌ Deleted |

### 5.2 Requirements Fulfillment

| Requirement | Fulfilled | Notes |
|-------------|-----------|-------|
| Survives rebuilds | ✅ Yes | Using named volumes |
| Survives database resets | ✅ Yes | Preserved by default |
| Survives container recreation | ✅ Yes | Named volumes persist |
| Survives image rebuilds | ✅ Yes | Volumes not tied to images |
| Purgeable when desired | ✅ Yes | `--purge-plugins` flag exists |

### 5.3 Stale Cache Risk

**Current State:** No automatic cache invalidation mechanism exists.

**Risk:** If a plugin's model format changes between versions, old cached data could cause errors.

**Recommendation:** Consider adding a cache version marker or timestamp that plugins can check.

---

## 6. Risk Analysis

### 6.1 Identified Risks

| Risk | Severity | Likelihood | Impact |
|------|----------|------------|--------|
| Old images accumulate (dangling) | Low | High | Wastes disk space |
| Build cache grows unbounded | Low | Medium | Wastes disk space |
| No Level 3 nuclear reset | Medium | N/A | Cannot fully clean environment |
| Stale plugin cache causing errors | Medium | Low | Hard to diagnose |
| Host-mounted library accidentally deleted | High | Very Low | User error, but devastating |

### 6.2 Risk Mitigation Status

| Risk | Current Mitigation | Recommendation |
|------|-------------------|----------------|
| Image accumulation | `docker system prune` in reset | Add explicit image pruning to Level 3 |
| Build cache growth | None | Add `docker builder prune` to Level 3 |
| No nuclear reset | `--purge-plugins` partial | Add `--nuclear` flag |
| Stale cache | None | Document cache clearing procedure |
| Library deletion | Read-only mount (`:ro`) | Good as-is |

---

## 7. Recommended Lifecycle Model

### 7.1 Proposed Command Structure

```
Level 1 - Rebuild:
    ./rebuild.sh                  # Standard rebuild
    ./rebuild.sh --clean-images   # Also prune dangling images

Level 2 - Database Reset:
    ./reset.sh                    # Reset DB + librarian-data
    ./reset.sh --include-artifacts  # Same (explicit)

Level 3 - Nuclear Reset:
    ./reset.sh --nuclear          # Full reset including plugins
    ./reset.sh --nuclear --include-images  # Also prune images
```

### 7.2 Data Behavior Summary

| Command | /library | PostgreSQL | /librarian-data | plugin_deps | plugin_cache | Images |
|---------|----------|-----------|-----------------|-------------|--------------|--------|
| `rebuild.sh` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `rebuild.sh --clean-images` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `reset.sh` | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| `reset.sh --nuclear` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `reset.sh --nuclear --include-images` | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |

### 7.3 Proposed Script Changes

#### rebuild.sh Additions
```bash
# Add --clean-images flag
REBUILD_CLEAN_IMAGES=false
if [ "$1" = "--clean-images" ]; then
    REBUILD_CLEAN_IMAGES=true
fi

# After rebuild completes:
if [ "$REBUILD_CLEAN_IMAGES" = true ]; then
    echo_status "Pruning dangling Docker images..."
    docker image prune -f
fi
```

#### reset.sh Restructuring
```bash
# Replace --purge-plugins with --nuclear
MODE="database-reset"  # default

for arg in "$@"; do
    case $arg in
        --nuclear)
            MODE="nuclear"
            ;;
        --include-images)
            CLEAN_IMAGES=true
            ;;
        --help)
            # Show usage with new options
            ;;
    esac
done

case $MODE in
    database-reset)
        # Current reset behavior
        docker volume rm librarian-postgres_data
        docker volume rm librarian-librarian_data
        ;;
    nuclear)
        # Nuclear reset: everything except library
        docker volume rm librarian-postgres_data
        docker volume rm librarian-librarian_data
        docker volume rm librarian-plugin_dependencies
        docker volume rm librarian-plugin_cache
        ;;
esac

# Optional image cleanup
if [ "$CLEAN_IMAGES" = true ]; then
    docker system prune -af
    docker builder prune -f
fi
```

---

## 8. Implementation Recommendations

### 8.1 Immediate Actions (Low Risk)

1. **Update script documentation** to reflect current behavior
2. **Add --help output** to reset.sh explaining all options
3. **Add version comment** to docker-compose volumes section

### 8.2 Medium-Term Improvements

1. **Add --nuclear flag** to reset.sh for Level 3 reset
2. **Add --clean-images flag** to rebuild.sh
3. **Add --include-images flag** to reset.sh --nuclear
4. **Update dev.sh** to expose new options

### 8.3 Long-Term Considerations

1. **Cache versioning mechanism** for plugins to detect stale caches
2. **Health check for volumes** to warn if volumes are corrupted
3. **Backup/restore script** for plugin dependencies
4. **Volume inspection commands** in status.sh

---

## 9. Current Script Behavior Quick Reference

### rebuild.sh
```
Preserves: ALL (library, postgres, librarian-data, plugin_deps, plugin_cache)
Destroys:  containers, build artifacts (but not images)
Images:    Rebuilt but not pruned
```

### reset.sh (default)
```
Preserves: /library, plugin_dependencies, plugin_cache
Destroys:  postgres_data, librarian_data, containers
Images:    Not touched
```

### reset.sh --purge-plugins
```
Preserves: /library only
Destroys:  ALL volumes (postgres, librarian-data, plugin_deps, plugin_cache), containers
Images:    Not touched (pruned by system prune)
```

### update.sh
```
Preserves: ALL (library, postgres, librarian-data, plugin_deps, plugin_cache)
Destroys:  containers
Images:    Pulled and rebuilt
```

---

## 10. Appendix: Command Reference

### Current Commands

| Command | Purpose |
|---------|---------|
| `./dev.sh update` | Delegates to update.sh |
| `./dev.sh rebuild` | Delegates to rebuild.sh |
| `./dev.sh reset` | Delegates to reset.sh |
| `./dev.sh status` | Delegates to status.sh |
| `./dev.sh logs` | Delegates to logs.sh |
| `./dev.sh smoke` | Delegates to smoke_test.sh |

### Docker Volume Names

| Volume | Full Name (with prefix) |
|--------|------------------------|
| postgres_data | librarian-postgres_data |
| librarian_data | librarian-librarian_data |
| plugin_dependencies | librarian-plugin_dependencies |
| plugin_cache | librarian-plugin_cache |

---

## 11. Conclusion

The current implementation has made significant progress toward the intended lifecycle model. The key findings are:

1. **Good:** Named volumes are correctly used for persistent data
2. **Good:** Plugin volumes are preserved by default in reset.sh
3. **Good:** `/library` is properly isolated as user-owned
4. **Needs Work:** Level 3 nuclear reset is not fully implemented
5. **Needs Work:** Image and build cache cleanup is incomplete
6. **Needs Work:** Script flags need standardization

The recommended path forward is to implement the `--nuclear` flag structure while maintaining backward compatibility with existing workflows.