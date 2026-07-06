# Runtime-First Debugging

This document defines the debugging priority order and establishes that runtime state always overrides configuration when the two contradict.

## Debugging Priority Order

When investigating issues, follow this priority sequence from top to bottom:

### 1. docker inspect

**Purpose:** Verify actual container configuration and runtime state.

```bash
docker inspect <container_name_or_id>
```

**What it reveals:**
- Actual command execution
- Mount bindings (critical for volume verification)
- Environment variables
- Network configuration
- Restart policy
- Resource limits

**Why first:** Container runtime state is the ground truth. It shows what Docker actually applied, which may differ from docker-compose files.

---

### 2. docker volume inspect

**Purpose:** Verify volume existence, mount points, and driver information.

```bash
docker volume inspect <volume_name>
```

**What it reveals:**
- Volume mountpoint on host
- Volume driver
- Volume labels
- Whether volume exists

**Why second:** Volumes persist data. If a volume doesn't exist or is mounted incorrectly, no amount of configuration changes will fix the issue.

---

### 3. docker logs

**Purpose:** Review application logs from within the container.

```bash
docker logs <container_name_or_id>
docker logs --tail 100 <container_name_or_id>
docker logs --since "2024-01-01" <container_name_or_id>
```

**What it reveals:**
- Application startup errors
- Runtime exceptions
- Processing failures
- Configuration errors at runtime

**Why third:** Logs show what the application actually experienced, not what was configured.

---

### 4. Database Queries

**Purpose:** Verify actual data state in PostgreSQL.

```bash
docker exec -it <container> psql -U librarian -d librarian
```

**What it reveals:**
- Document records existence
- Checksum verification status
- Artifact path references
- Processing state flags

**Why fourth:** Database queries reveal the authoritative metadata state, which may differ from application assumptions.

---

### 5. Filesystem Inspection

**Purpose:** Verify actual files exist where expected.

```bash
# Inside container
docker exec -it <container> ls -la /library
docker exec -it <container> ls -la /librarian-data

# On host
docker volume inspect <volume> --format '{{.Mountpoint}}'
ls -la <mountpoint>
```

**What it reveals:**
- Whether evidence files exist
- Whether artifact files exist
- File permissions
- Directory structure

**Why fifth:** Filesystem inspection confirms whether data actually exists, independent of database records or configuration.

---

### 6. Source Code Inspection

**Purpose:** Understand intended behavior and implementation details.

```bash
# Search for relevant code
grep -r "thumbnail" /app/workers/
grep -r "mount" /app/
```

**What it reveals:**
- Expected file paths
- Processing logic
- Configuration expectations

**Why last:** Source code shows intent, not reality. Use code to understand what *should* happen, then use runtime inspection to verify what *is* happening.

---

## Runtime Evidence Hierarchy

Runtime evidence always overrides other sources of truth. When there is a contradiction, trust the highest-priority source:

| Priority | Source | Override Strength |
|----------|--------|------------------|
| 1 | `docker inspect` | Overrides docker-compose |
| 2 | `docker volume inspect` | Overrides mount assumptions |
| 3 | `docker logs` | Overrides application assumptions |
| 4 | Database query | Overrides ORM model defaults |
| 5 | Filesystem `ls` | Overrides configuration paths |
| 6 | Source code | Intent only, lowest authority |

---

## Common Contradictions and Resolution

### Contradiction: docker-compose vs docker inspect

**Scenario:** docker-compose.yml shows `/library:/data`, but thumbnails are missing.

**Resolution:**
```bash
# Get actual mount from docker inspect
docker inspect librarian | jq '.[0].Mounts'

# Compare with docker-compose
cat docker-compose.yml | grep -A5 library
```

**Decision:** Always use `docker inspect` output. Configuration files may be stale or overridden.

---

### Contradiction: Database record vs filesystem

**Scenario:** Database shows `thumbnail_path = /librarian-data/thumbnails/123.jpg`, but file doesn't exist.

**Resolution:**
```bash
# Verify filesystem
docker exec librarian ls -la /librarian-data/thumbnails/123.jpg

# Check volume mount
docker volume inspect librarian_librarian-data
```

**Decision:** Filesystem state is authoritative for file existence. Missing files indicate volume mount issues or cleanup, not database errors.

---

### Contradiction: Source code path vs actual mount

**Scenario:** Code references `/data/library`, but runtime mount is `/library`.

**Resolution:**
```bash
# Get actual mount
docker inspect librarian | jq '.[0].Mounts[] | select(.Destination=="/library")'
```

**Decision:** Runtime mount configuration is authoritative. Code may be outdated or have environment-specific overrides.

---

## Investigation Workflow

### Step 1: Verify Container State
```bash
docker inspect <container> --format '{{json .State}}'
docker inspect <container> --format '{{json .Mounts}}'
```

### Step 2: Verify Volumes
```bash
docker volume ls
docker volume inspect <volume_name>
```

### Step 3: Verify Logs
```bash
docker logs --tail 50 <container>
docker logs --since "1h" <container> | grep -i error
```

### Step 4: Verify Database
```sql
SELECT id, path, sha256, thumbnail_path FROM documents LIMIT 10;
```

### Step 5: Verify Filesystem
```bash
docker exec <container> ls -la /library
docker exec <container> ls -la /librarian-data
```

### Step 6: Document Findings
Record the contradiction between expected and actual state before proposing any fixes.

---

## Golden Rule

> **Never propose a fix before proving the runtime state.**

1. Inspect before hypothesizing
2. Verify before fixing
3. Document contradictions before resolving them
4. Trust runtime over configuration every time

---

## Example Investigation

**Problem:** User reports thumbnails are not displaying.

**Wrong approach:** Assume the thumbnail generator is broken and look at the code.

**Correct approach:**

1. `docker inspect` — Verify container is running with correct mounts
2. `docker volume inspect` — Verify librarian-data volume exists
3. `docker logs` — Check for thumbnail generation errors
4. Database query — Verify document records have thumbnail_path set
5. Filesystem check — Verify thumbnail files exist in volume
6. Source code — Only after runtime state is known

This sequence quickly identifies whether the issue is:
- Volume not mounted (docker inspect)
- Volume empty (volume inspect)
- Processing failure (logs)
- Missing database record (query)
- Missing file (filesystem)
- Code bug (source code, last resort)