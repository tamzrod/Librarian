# Runtime-First Investigation Rules

This document defines the rules AI agents must follow when investigating issues in the Librarian system. These rules prevent common investigative errors and ensure accurate root cause analysis.

## Core Principle

> **Runtime state always overrides code assumptions, configuration files, and documentation.**

When there is a contradiction between what is documented/configured and what actually exists at runtime, trust the runtime evidence first.

---

## Investigation Rules

### Rule 1: Runtime State Overrides Code Assumptions

**Statement:** The actual state of running containers, volumes, databases, and filesystems takes precedence over what the code assumes or expects.

**Why:** Code reflects intended behavior, not necessarily actual behavior. Runtime state reflects what is actually happening.

**Application:**
```
Code says: thumbnails are stored in /librarian-data/thumbnails
Runtime shows: /librarian-data is not mounted to the container

Decision: Trust runtime. The volume is not mounted.
```

**Command to verify:**
```bash
docker inspect librarian --format '{{json .Mounts}}'
```

---

### Rule 2: docker inspect Overrides docker-compose

**Statement:** The output of `docker inspect` is the authoritative source of container configuration, not the docker-compose.yml file.

**Why:** docker-compose is a deployment specification. docker inspect shows what Docker actually applied, including any runtime overrides, environment variable expansions, or configuration drift.

**Application:**
```
docker-compose shows: /library:/data
docker inspect shows: /home/user/library:/data

Decision: Trust docker inspect. The actual mount is /home/user/library.
```

**Command to verify:**
```bash
docker inspect <container_name> | jq '.[0].Mounts'
```

---

### Rule 3: Database Rows Override ORM Models

**Statement:** The actual contents of database rows take precedence over model definitions, default values, and ORM assumptions.

**Why:** ORM models define the schema and defaults, but the actual data may have been inserted with different values, migrated incorrectly, or corrupted.

**Application:**
```
Model defines: thumbnail_path nullable=True
Database has: thumbnail_path = '/path/to/file'
Filesystem: file does not exist

Decision: Database record shows path was recorded, but file is missing.
```

**Commands to verify:**
```bash
docker exec <container> psql -U librarian -d librarian -c "SELECT id, path, thumbnail_path FROM documents LIMIT 5;"
docker exec <container> ls -la /librarian-data/thumbnails/
```

---

### Rule 4: Filesystem State Overrides Expected Paths

**Statement:** The actual existence (or non-existence) of files and directories on the filesystem takes precedence over configured paths, hardcoded paths, and documentation.

**Why:** Configuration errors, volume mount issues, or cleanup operations may have moved or deleted files. Always verify filesystem state before assuming paths are correct.

**Application:**
```
Config expects: /library/photos/vacation.jpg
Filesystem shows: /library/photos/ does not exist

Decision: Directory does not exist. Either mount is wrong or data is missing.
```

**Commands to verify:**
```bash
docker exec <container> ls -la /library/
docker exec <container> find /librarian-data -name "*.jpg" 2>/dev/null | head -20
```

---

### Rule 5: Never Propose Fixes Before Proving Runtime State

**Statement:** Before suggesting any fix, modification, or remediation, first verify the actual runtime state of all relevant components.

**Why:** Premature fixes based on assumptions often address the wrong problem. Proving the runtime state ensures the fix targets the actual issue.

**Workflow:**
1. Inspect containers (docker inspect)
2. Inspect volumes (docker volume inspect)
3. Check logs (docker logs)
4. Query database
5. Verify filesystem
6. Only then: propose fix based on evidence

**Anti-pattern:**
```
User: Thumbnails aren't showing
Agent: Let me fix the thumbnail generator code...

WRONG. Agent should first verify:
- Is /librarian-data volume mounted?
- Are thumbnail files being generated?
- Are database records being created?
```

---

### Rule 6: Never Infer Mounts from Configuration Files

**Statement:** Do not assume that because docker-compose.yml defines a volume mount, that mount is actually active in the running container. Always verify with `docker inspect`.

**Why:** Common failure modes include:
- Volume not created before container started
- Volume mount overridden by command line
- Docker configuration errors
- Volume driver issues

**Application:**
```
docker-compose.yml defines: librarian-data volume mount
docker inspect shows: Mounts array is empty

Decision: Volume is NOT mounted, despite configuration.
```

**Commands to verify:**
```bash
# Check actual mounts
docker inspect <container> --format '{{json .Mounts}}' | jq

# Check volume exists
docker volume ls | grep librarian

# Check volume details
docker volume inspect librarian_librarian-data
```

---

## Investigation Checklist

For every issue investigation:

### Phase 1: Verify Container Runtime
- [ ] Container is running: `docker ps | grep <name>`
- [ ] Container has correct mounts: `docker inspect | jq '.[0].Mounts'`
- [ ] Container has correct environment: `docker inspect | jq '.[0].Config.Env'`
- [ ] Container is healthy: `docker inspect | jq '.[0].State.Health'`

### Phase 2: Verify Volumes
- [ ] Volume exists: `docker volume ls`
- [ ] Volume has correct driver: `docker volume inspect`
- [ ] Volume mountpoint is accessible: `ls -la <mountpoint>`

### Phase 3: Verify Application State
- [ ] Application logs show no errors: `docker logs --tail 100`
- [ ] Application is responding: `curl http://localhost:port/health`
- [ ] Database is accessible: `docker exec psql ...`

### Phase 4: Verify Data State
- [ ] Database has expected records: `SELECT COUNT(*) FROM documents`
- [ ] Files exist where records say: `ls <path>` for each artifact_path
- [ ] Checksums match: `sha256sum` on evidence files

### Phase 5: Propose Fix
- [ ] Document the contradiction between expected and actual
- [ ] Propose fix that addresses the actual root cause
- [ ] Verify fix doesn't break other components

---

## Common Investigation Errors

### Error 1: Trusting Configuration Over Runtime

**Wrong:**
```
docker-compose.yml shows /library mount
Agent assumes /library is mounted
Agent doesn't check docker inspect
```

**Correct:**
```
docker-compose.yml shows /library mount
Agent runs docker inspect
Agent verifies /library is actually in Mounts array
```

### Error 2: Assuming Files Exist Because Records Exist

**Wrong:**
```
Database shows thumbnail_path = '/librarian-data/thumbnails/123.jpg'
Agent assumes thumbnail exists
Agent doesn't check filesystem
```

**Correct:**
```
Database shows thumbnail_path = '/librarian-data/thumbnails/123.jpg'
Agent runs docker exec ls /librarian-data/thumbnails/123.jpg
Agent discovers file is missing
Agent investigates volume mount issue
```

### Error 3: Modifying Code Before Understanding Runtime

**Wrong:**
```
Error: thumbnails not displaying
Agent assumes thumbnail generator is broken
Agent starts modifying thumbnail_generator.py
```

**Correct:**
```
Error: thumbnails not displaying
Agent runs docker inspect to verify mounts
Agent runs docker volume inspect to verify volumes
Agent checks logs for errors
Agent queries database for thumbnail_path values
Agent checks filesystem for thumbnail files
Agent discovers /librarian-data is not mounted
```

---

## Evidence Priority Table

| Evidence Type | Priority | Override Strength |
|---------------|----------|-------------------|
| docker inspect output | 1 (Highest) | Overrides docker-compose |
| docker volume inspect | 2 | Overrides volume assumptions |
| docker logs | 3 | Overrides application code |
| Database query results | 4 | Overrides ORM models |
| Filesystem ls/find output | 5 | Overrides configured paths |
| Source code comments | 6 | Lowest authority |
| Documentation | 7 | Can be outdated |

---

## Summary

1. **Inspect before assuming** — Always verify runtime state
2. **Runtime over configuration** — docker inspect > docker-compose
3. **Filesystem over records** — Verify files exist
4. **Database over models** — Query actual data
5. **Prove before fixing** — Document actual state before proposing solutions
6. **Never infer mounts** — Always verify with docker inspect