# API Migration Guide

This guide documents breaking changes and migration procedures for the Librarian API.

## Migration Philosophy

1. **Minimize Disruption** - Provide clear migration paths
2. **Backward Compatibility** - Support old patterns where possible
3. **Clear Communication** - Document all changes thoroughly

## v1.0 to v2.0 (Planned)

_This section will be populated when v2.0 is developed._

### Planned Breaking Changes

- [ ] Authentication/Authorization
- [ ] Pagination format changes
- [ ] Response envelope standardization
- [ ] Batch operation endpoints

### Migration Steps

When v2.0 is released:

1. **Update Dashboard API Version**
   ```typescript
   // dashboard/src/config/api.ts
   export const API_VERSION = 'v2.0'
   ```

2. **Review Breaking Changes**
   - Check the breaking changes section above
   - Update any affected API calls
   - Update type definitions

3. **Test Migration**
   - Run integration tests
   - Validate all dashboard features work
   - Check error handling for new error codes

4. **Deploy**
   - Deploy new API version
   - Deploy updated dashboard
   - Monitor for issues

## Dashboard Compatibility Matrix

| Dashboard Version | API Version | Compatible |
|------------------|-------------|------------|
| 1.0.0 | v1.0 | ✅ Yes |
| 1.0.0 | v2.0 | ❌ No |
| 2.0.0 | v1.0 | ⚠️ Legacy |
| 2.0.0 | v2.0 | ✅ Yes |

## Error Handling During Migration

During API version transitions, the dashboard should handle:

### 404 Not Found
```typescript
// Old endpoint removed in new version
// Redirect to new endpoint or show deprecation notice
```

### 400 Validation Error
```typescript
// New validation rules may reject old patterns
// Update request format
```

### 503 Service Unavailable
```typescript
// API may be temporarily unavailable during deploy
// Implement retry logic with exponential backoff
```

## Rollback Procedure

If migration fails:

1. **Revert Dashboard**
   ```bash
   git revert <dashboard-commit>
   ```

2. **Keep Old API Running**
   ```bash
   docker compose stop librarian-api
   docker compose rm librarian-api
   # Restore previous version
   ```

3. **Monitor**
   - Check error rates
   - Verify old endpoints work
   - Contact support if issues persist

## Contact

For migration support:
- API Issues: [API Repository Issues]
- Dashboard Issues: [Dashboard Repository Issues]
