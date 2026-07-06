# Risk Analysis

**Purpose:** Document risks and mitigations for Operation Plugin Foundation

---

## Risk Assessment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RISK ASSESSMENT MATRIX                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  IMPACT                                                                      │
│      │                                                                        │
│  5   │  ████████████████████████████████  HIGH                            │
│      │                                                                        │
│  4   │  ████████████████████████████████  HIGH                            │
│      │                                                                        │
│  3   │  ████████████████████████████████  MEDIUM                          │
│      │                                                                        │
│  2   │  ████████████████████████████████  LOW                            │
│      │                                                                        │
│  1   │  ████████████████████████████████  LOW                            │
│      │                                                                        │
│      └───────────────────────────────────────────────────────────────────    │
│           1       2       3       4       5                                │
│                            LIKELIHOOD                                          │
│                                                                             │
│  Risk Score = Impact × Likelihood                                           │
│  ████████████████████████████████  = Critical (>15)                        │
│  ████████████████████████████████  = High (10-15)                         │
│  ████████████████████████████████  = Medium (5-10)                        │
│  ████████████████████████████████  = Low (<5)                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Identified Risks

### Risk 1: UNIQUE Constraint Breaking Change

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-001 |
| **Category** | Database |
| **Description** | Changing UNIQUE constraint from `document_id` to `(document_id, plugin_name, engine_name)` may cause issues with existing data |
| **Likelihood** | 2 (Unlikely) |
| **Impact** | 4 (High) |
| **Risk Score** | 8 (Medium) |

**Mitigation:**
1. Use `IF NOT EXISTS` for constraint creation
2. Test migration on copy of production data
3. Have rollback plan ready
4. Schedule during low-traffic period

**Contingency:**
```sql
-- Rollback: Restore old constraint
ALTER TABLE photo_metadata 
    DROP CONSTRAINT IF EXISTS uq_photo_metadata_identity;
ALTER TABLE photo_metadata 
    ADD CONSTRAINT photo_metadata_document_id_key
    UNIQUE (document_id);
```

---

### Risk 2: Existing Data Not Backfilled

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-002 |
| **Category** | Data |
| **Description** | Backfill of identity columns may fail or be incomplete |
| **Likelihood** | 3 (Possible) |
| **Impact** | 3 (Medium) |
| **Risk Score** | 9 (Medium) |

**Mitigation:**
1. Run backfill as separate step
2. Verify all rows backfilled
3. Add validation query
4. Log backfill progress

**Contingency:**
```python
# Re-run backfill
def backfill_identities():
    """Re-backfill identity columns."""
    
    # Find rows without identity
    missing = query("""
        SELECT document_id FROM photo_metadata
        WHERE plugin_name IS NULL
    """)
    
    # Backfill each
    for row in missing:
        update_photo_metadata(row.document_id, {
            'plugin_name': 'metadata.exif.pillow',
            'engine_name': 'pillow-exif',
            'plugin_version': '1.0.0'
        })
```

---

### Risk 3: API Breaking Changes

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-003 |
| **Category** | API |
| **Description** | Adding new fields to API responses may break existing clients |
| **Likelihood** | 4 (Likely) |
| **Impact** | 3 (Medium) |
| **Risk Score** | 12 (High) |

**Mitigation:**
1. Add fields as optional
2. Use backward-compatible response format
3. Version API if needed
4. Document changes in release notes

**Contingency:**
```python
# Add optional parameter for legacy clients
GET /api/v1/photo-metadata/{id}?include_provenance=false

# Default to include_provenance=true for new clients
```

---

### Risk 4: Worker Compatibility

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-004 |
| **Category** | Code |
| **Description** | Existing workers may not set identity fields |
| **Likelihood** | 3 (Possible) |
| **Impact** | 3 (Medium) |
| **Risk Score** | 9 (Medium) |

**Mitigation:**
1. Use DEFAULT values in database
2. Validate in BaseWorker
3. Add test for identity
4. Document requirements

**Contingency:**
```python
# Worker validation
class BaseWorker:
    def process(self, job):
        if not self.plugin_name:
            raise ValueError("Worker must set plugin_name")
        # ...
```

---

### Risk 5: Query Performance Degradation

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-005 |
| **Category** | Performance |
| **Description** | New columns and indexes may affect query performance |
| **Likelihood** | 2 (Unlikely) |
| **Impact** | 2 (Low) |
| **Risk Score** | 4 (Low) |

**Mitigation:**
1. Use appropriate indexes
2. Test query performance
3. Monitor slow queries
4. Optimize if needed

**Contingency:**
- Fine-tune indexes
- Optimize queries

---

### Risk 6: Migration Failure

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-006 |
| **Category** | Database |
| **Description** | Migration may fail mid-execution |
| **Likelihood** | 1 (Rare) |
| **Impact** | 5 (Critical) |
| **Risk Score** | 5 (Medium) |

**Mitigation:**
1. Test migration thoroughly
2. Have full backup
3. Use transaction where possible
4. Prepare rollback procedures

**Contingency:**
```bash
# Restore from backup
pg_restore -h localhost -U postgres -d librarian backup.sql
```

---

## Risk Summary Matrix

| Risk ID | Risk | Category | Impact | Likelihood | Score | Mitigation |
|---------|------|----------|--------|------------|-------|------------|
| R-001 | UNIQUE constraint change | Database | 4 | 2 | 8 | Test, rollback |
| R-002 | Data not backfilled | Data | 3 | 3 | 9 | Validation |
| R-003 | API breaking changes | API | 3 | 4 | 12 | Optional fields |
| R-004 | Worker compatibility | Code | 3 | 3 | 9 | Defaults |
| R-005 | Query performance | Performance | 2 | 2 | 4 | Indexes |
| R-006 | Migration failure | Database | 5 | 1 | 5 | Backup, rollback |

---

## Risk Distribution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RISK DISTRIBUTION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  High (Score 10+)                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │  R-003: API breaking changes                                       │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Medium (Score 5-10)                                                      │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │  R-002: Data not backfilled                                       │   │
│  │  R-004: Worker compatibility                                      │   │
│  │  R-001: UNIQUE constraint change                                   │   │
│  │  R-006: Migration failure                                         │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Low (Score < 5)                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │  R-005: Query performance                                         │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Mitigation Priority

### Before Implementation

| Priority | Action | Risks Addressed |
|----------|--------|----------------|
| 1 | Full database backup | R-001, R-006 |
| 2 | Test migration on staging | R-001, R-002, R-006 |
| 3 | Review API compatibility | R-003 |
| 4 | Add DEFAULT values | R-004 |

### During Implementation

| Priority | Action | Risks Addressed |
|----------|--------|----------------|
| 1 | Run migration in transaction | R-006 |
| 2 | Verify backfill | R-002 |
| 3 | Run existing tests | R-004 |
| 4 | Monitor performance | R-005 |

### After Implementation

| Priority | Action | Risks Addressed |
|----------|--------|----------------|
| 1 | Verify all tests pass | All |
| 2 | Review API compatibility | R-003 |
| 3 | Check query performance | R-005 |
| 4 | Document changes | R-003 |

---

## Monitoring

### Metrics to Watch

| Metric | Warning | Critical |
|--------|---------|----------|
| Migration duration | > 5 min | > 15 min |
| Test failures | > 0 | > 5 |
| API error rate | > 1% | > 5% |
| Query latency | > 200ms | > 500ms |

### Alert Rules

```yaml
- alert: MigrationFailed
  expr: librarian_migration_failures > 0
  for: 1m
  labels:
    severity: critical

- alert: TestFailures
  expr: rate(librarian_test_failures[5m]) > 0
  for: 5m
  labels:
    severity: warning
```

---

## Sign-off Checklist

### Pre-Implementation

- [ ] All risks have mitigation plans
- [ ] Backup verified
- [ ] Staging test complete
- [ ] Rollback procedures documented

### Implementation

- [ ] Migration validated
- [ ] Backfill complete
- [ ] Tests passing
- [ ] API compatible

### Post-Implementation

- [ ] Performance verified
- [ ] Documentation updated
- [ ] No regressions
- [ ] Team briefed

---

## Summary

| Aspect | Assessment |
|--------|------------|
| Overall Risk | Low-Medium |
| Critical Risks | 0 |
| High Risks | 1 (API breaking) |
| Medium Risks | 4 |
| Low Risks | 1 |

**Conclusion:** Operation Plugin Foundation has manageable risks. Primary concern is API compatibility, which can be addressed with optional fields.
