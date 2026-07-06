# Derived Artifact Recovery

## Overview

This document describes the derived artifact recovery system for Librarian. The system provides detection and repair capabilities for missing or orphaned derived artifacts such as thumbnails, embeddings, OCR results, and object detection data.

## Architecture Principles

### Core Tenets

1. **Artifact is authoritative**: The filesystem contains ground truth for derived artifacts.
2. **Metadata is a cache**: Database records are regeneratable from source artifacts.
3. **Selective repair**: Only missing artifacts are repaired; healthy artifacts are never regenerated.
4. **Idempotent operations**: Recovery can be run multiple times safely.

### Design Philosophy

Derived artifacts (thumbnails, embeddings, OCR, etc.) are:
- **Optional**: The system functions without them; they enhance but don't block operation
- **Recoverable**: Any derived artifact can be regenerated from its source
- **Volatile**: May be lost due to volume deletion, plugin upgrades, or accidental deletion

The database contains metadata (paths, references) that becomes stale when artifacts are lost. Recovery synchronizes the metadata with filesystem reality.

## Artifact Types

The system supports recovery for the following artifact types:

| Artifact Type | Storage Location | Metadata Field | Supported Documents |
|---------------|-----------------|----------------|---------------------|
| thumbnail | `/librarian-data/thumbnails/` | `documents.thumbnail_path` | images, videos |
| embedding | `/librarian-data/embeddings/` | `documents.embedding_path` | text, structured |
| ocr | `/librarian-data/ocr/` | `documents.ocr_path` | images, documents |
| object_detection | `/librarian-data/detections/` | `documents.detection_path` | images, videos |
| transcription | `/librarian-data/transcriptions/` | `documents.transcription_path` | audio, video |

## Detection Workflow

### Purpose

Detection identifies the state of all artifacts without making changes. It categorizes artifacts as:

- **VALID**: Both metadata and file exist and match
- **MISSING**: Metadata exists but file is missing (orphaned metadata)
- **ORPHAN**: File exists but no metadata reference
- **PENDING**: Neither metadata nor file exists (expected state for unprocessed documents)

### Detection Process

```
1. List all files in artifact storage directory
   ↓
2. Query database for all artifact metadata records
   ↓
3. For each metadata record:
   - If file exists → VALID
   - If file missing → MISSING
   ↓
4. For each filesystem file:
   - If not referenced in metadata → ORPHAN
```

### Example Output

```
================================================================
Detection Results: thumbnail
================================================================
  Total documents scanned:     5591
  Total files on disk:        1
  Valid artifacts:             1
  Missing artifacts:           5590
  Orphan files:                0
  Health percentage:           0.02%
```

## Recovery Workflow

### Purpose

Recovery repairs missing artifacts by:
1. Clearing stale metadata
2. Requeuing generation jobs

### Recovery Process

```
1. Run detection to identify MISSING artifacts
   ↓
2. For each MISSING artifact:
   a. Clear thumbnail_path in documents table (set to NULL)
   b. Cancel any existing queued/in-progress jobs for this artifact
   c. Create new job with priority 50 (medium priority)
   ↓
3. Report results (repaired, failed, skipped)
```

### Safety Mechanisms

- **Dry-run mode**: Always run with `--dry-run` first to preview changes
- **Selective repair**: Only MISSING artifacts are touched
- **No deletion**: Orphan files are reported but not automatically deleted
- **Idempotent**: Can be run multiple times safely

## CLI Usage

### List Available Artifact Types

```bash
python -m core.cli list
```

Output:
```
Available artifact types for recovery:

  Artifact Type          Handler                
  --------------------   --------------------
  thumbnail              ThumbnailRecovery     
```

### Detect Artifact State

```bash
# Detect thumbnails (default)
python -m core.cli detect thumbnail

# Detect with verbose output
python -m core.cli detect thumbnail -v

# Detect with custom database connection
python -m core.cli detect thumbnail --db-host localhost --db-port 5432
```

### Repair Missing Artifacts

```bash
# Dry run (default) - shows what would be done
python -m core.cli repair thumbnail

# Execute repairs
python -m core.cli repair thumbnail --fix
```

## Expected States

### Healthy State

After successful recovery:

```
================================================================
Detection Results: thumbnail
================================================================
  Total documents scanned:     5591
  Total files on disk:        5591
  Valid artifacts:             5591
  Missing artifacts:           0
  Orphan files:                0
  Health percentage:           100.0%
```

### Post-Recovery Job Queue

After repair, jobs are queued for regeneration:

| Priority | Purpose | Typical Source |
|----------|---------|----------------|
| 100 | Viewport thumbnails | User browsing |
| 50 | Recovered artifacts | Recovery repair |
| 10 | Background generation | Initial processing |

Workers will process priority 50 jobs as they become available.

## Failure Modes

### Detection Failures

| Failure | Cause | Resolution |
|---------|-------|------------|
| Cannot connect to database | PostgreSQL unavailable | Check database connectivity |
| Cannot list storage directory | Volume not mounted | Verify `/librarian-data` is mounted |
| Query timeout | Large database | Use pagination or increase timeout |

### Recovery Failures

| Failure | Cause | Resolution |
|---------|-------|------------|
| Cannot clear metadata | Database constraint | Manual database update required |
| Cannot requeue job | Duplicate job exists | Already handled by job cancellation |
| Source file missing | Document deleted | Artifact cannot be recovered; metadata cleared |

### Recovery Scenarios

#### Lost Thumbnails Volume

**Symptom**: Detection shows all thumbnails MISSING
```
Missing artifacts: 5590
Health percentage: 0.02%
```

**Recovery**:
1. Mount new `/librarian-data` volume
2. Run `python -m core.cli repair thumbnail --fix`
3. Workers regenerate all thumbnails

**Timeline**: Depends on worker capacity; can take hours for large libraries

#### Partial Volume Loss

**Symptom**: Detection shows some thumbnails MISSING
```
Missing artifacts: 500
Health percentage: 91.1%
```

**Recovery**:
1. Run `python -m core.cli repair thumbnail --fix`
2. Only 500 jobs are requeued

#### Plugin Upgrade

**Symptom**: New plugin version generates incompatible artifacts
```
Valid artifacts: 5591 (may be corrupted by new version)
Orphan files: 5591 (old format)
```

**Recovery**:
1. Plan: Decide whether to regenerate or keep old artifacts
2. If regenerating: Clear metadata, then run repair
3. New jobs will use new plugin version

## Runtime Validation

### Quick Health Check

```bash
# Check thumbnail health
python -m core.cli detect thumbnail | grep "Health percentage"
```

### Detailed Validation

```bash
# Full detection with verbose output
python -m core.cli detect thumbnail -v
```

### Integration Testing

To verify the recovery system works:

1. Create a test document
2. Generate its thumbnail
3. Verify thumbnail exists
4. Manually delete the thumbnail file
5. Run detection - should show 1 MISSING
6. Run repair
7. Verify job is queued
8. Wait for worker to process
9. Verify thumbnail regenerated

## API Integration

For programmatic access, use the recovery module directly:

```python
from storage.postgres_backend import PostgresBackend
from core.recovery import get_recovery_handler

backend = PostgresBackend()
handler = get_recovery_handler('thumbnail', backend)

# Detect
report = handler.detect()
print(f"Missing: {len(report.missing)}")

# Repair
if report.missing:
    handler.repair(report.missing, dry_run=False)

backend.close()
```

## Extending the Framework

To add support for a new artifact type:

1. Create a new class inheriting from `BaseArtifactRecovery`
2. Implement required abstract methods
3. Register in `RECOVERY_HANDLERS` dict

```python
class EmbeddingRecovery(BaseArtifactRecovery):
    ARTIFACT_TYPE = "embedding"
    ARTIFACT_SUBDIR = "embeddings"

    def get_artifact_metadata(self):
        # Query embeddings table
        pass

    def get_artifact_path_field(self):
        return "embedding_path"

    def is_supported_artifact(self, document_id):
        # Check if text/structured type
        pass

    def clear_artifact_metadata(self, document_id):
        # Clear embedding_path
        pass

    def requeue_artifact_job(self, document_id):
        # Requeue generate_embeddings job
        pass
```

## Security Considerations

- **Read-only detection**: Detection queries only; no modifications
- **Controlled repairs**: Only metadata cleared and jobs requeued
- **No file deletion**: Orphan files are never automatically deleted
- **Audit trail**: All operations logged with document IDs

## Monitoring

### Log Format

```
2024-01-15 10:30:00 - INFO - Detection complete: 1 valid, 5590 missing, 0 orphans for thumbnail
2024-01-15 10:30:05 - INFO - Cleared metadata for document 1234
2024-01-15 10:30:05 - INFO - Requeued job 5678 for document 1234
```

### Metrics to Track

- `librarian_artifact_health{type}`: Health percentage per artifact type
- `librarian_artifact_missing{type}`: Count of missing artifacts
- `librarian_recovery_jobs_created{type}`: Jobs created by recovery

## Troubleshooting

### "Cannot open directory" Error

**Cause**: `/librarian-data` volume not mounted

**Solution**:
```bash
# Check if directory exists
ls -la /librarian-data

# Check volume mounts in docker-compose
docker inspect librarian-api | grep -A10 Mounts
```

### "Zero valid artifacts" Warning

**Cause**: Expected state after volume loss

**Solution**: Run recovery to requeue missing artifacts

### Recovery Jobs Not Processing

**Cause**: Workers may be paused or scaled to zero

**Solution**:
```bash
# Check worker status
docker ps | grep librarian-worker

# Check job queue
curl http://localhost:8001/api/v1/jobs/status
```

## References

- [Artifact Inventory Model](../architecture/artifact-inventory.md)
- [Operation Plugin Foundation](./operation-plugin-foundation/)
- [Deployment Lifecycle Audit](./deployment-lifecycle-audit.md)
