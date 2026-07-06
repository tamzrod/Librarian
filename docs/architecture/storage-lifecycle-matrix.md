# Storage Lifecycle Matrix

This document defines the expected behavior of each storage component across the three operational reset modes: `rebuild.sh`, `reset.sh`, and `nuclear reset`.

## Reset Modes Overview

### rebuild.sh

Full application rebuild while preserving evidence and user data. Used for major version upgrades or configuration changes.

### reset.sh

Soft reset that clears derived artifacts and application state while preserving original documents and evidence.

### Nuclear Reset

Complete data wipe including evidence, artifacts, and database. Used as last resort when corruption is suspected.

---

## Lifecycle Matrix

| Asset | Tier | Rebuild | Reset | Nuclear |
|-------|------|---------|-------|---------|
| `library` | 0 - Evidence | **keep** | **keep** | **delete** |
| `postgres` | 0 - Evidence | **keep** | **delete** | **delete** |
| `librarian-data` | 1 - Artifacts | **keep** | **delete** | **delete** |
| `plugin-dependencies` | 2 - Infrastructure | **keep** | **keep** | **delete** |
| `plugin-cache` | 2 - Infrastructure | **keep** | **keep** | **delete** |

---

## Detailed Asset Specifications

### library

**Description:** Mounted directory containing original source documents and media files.

**Tier:** 0 (Evidence - Authoritative)

| Operation | Behavior | Rationale |
|-----------|----------|-----------|
| Rebuild | Keep | Evidence is preserved for reprocessing |
| Reset | Keep | Evidence survives all non-nuclear resets |
| Nuclear | Delete | Only nuclear reset destroys evidence |

**Danger Level:** CRITICAL - Data loss is irreversible

---

### postgres

**Description:** Database containing document metadata, extracted entities, and system state.

**Tier:** 0 (Evidence - Authoritative)

| Operation | Behavior | Rationale |
|-----------|----------|-----------|
| Rebuild | Keep | Database state preserved across rebuilds |
| Reset | Delete | Clears database to allow fresh indexing |
| Nuclear | Delete | Complete state wipe |

**Danger Level:** HIGH - Contains evidence metadata and integrity checksums

---

### librarian-data

**Description:** Derived artifacts volume including thumbnails, embeddings, OCR output, and processing cache.

**Tier:** 1 (Derived Artifacts - Regeneratable)

| Operation | Behavior | Rationale |
|-----------|----------|-----------|
| Rebuild | Keep | Preserves derived data across rebuilds |
| Reset | Delete | Forces regeneration of all artifacts |
| Nuclear | Delete | Artifacts are not preserved in nuclear reset |

**Danger Level:** MEDIUM - Loss is recoverable through reprocessing

---

### plugin-dependencies

**Description:** Installed Python packages and plugin-specific dependencies.

**Tier:** 2 (Plugin Infrastructure)

| Operation | Behavior | Rationale |
|-----------|----------|-----------|
| Rebuild | Keep | Dependencies preserved across rebuilds |
| Reset | Keep | Dependencies survive standard resets |
| Nuclear | Delete | Full dependency reinstall in nuclear reset |

**Danger Level:** LOW - Regenerated from requirements/manifests

---

### plugin-cache

**Description:** Runtime caches, compiled Python bytecode, and plugin-specific caches.

**Tier:** 2 (Plugin Infrastructure)

| Operation | Behavior | Rationale |
|-----------|----------|-----------|
| Rebuild | Keep | Cache preserved for performance |
| Reset | Keep | Cache survives standard resets |
| Nuclear | Delete | Cache cleared in nuclear reset |

**Danger Level:** LOW - Regenerated on first use

---

## Operational Checklist

### Before any reset operation:

- [ ] Verify what tier each asset belongs to
- [ ] Confirm backup status of Tier 0 assets
- [ ] Document current artifact state for comparison after reset

### After rebuild:

- [ ] Verify library contents are intact
- [ ] Verify database connections work
- [ ] Verify plugin dependencies are loaded

### After reset:

- [ ] Confirm library was preserved
- [ ] Confirm database was cleared
- [ ] Confirm librarian-data was cleared
- [ ] Verify artifacts can be regenerated on demand

### After nuclear reset:

- [ ] Confirm all data has been wiped
- [ ] Verify fresh plugin installation
- [ ] Begin fresh indexing from library

---

## Error States and Diagnostics

### Unexpected data loss after rebuild

1. Check if library mount is correctly configured
2. Verify volume mounts in docker-compose
3. Use `docker volume inspect` to verify volume contents
4. Cross-reference with database records

### Unexpected data persistence after reset

1. Use `docker volume inspect` to verify actual volume state
2. Check for volume mount misconfigurations
3. Verify no symlinks or bind mounts are preserving data
4. Compare runtime container state with configuration

### Volume state contradicts configuration

1. **Always trust runtime state over configuration files**
2. Use `docker inspect` to verify actual container mounts
3. Use `docker volume inspect` to verify volume existence
4. Document discrepancy before attempting any fixes