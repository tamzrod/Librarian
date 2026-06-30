# Librarian API Contract

**Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2026-06-29

---

## Overview

This directory contains the API contract documentation for the Librarian API. The API is the single source of truth for all data access between the backend and dashboard.

## Contract Principles

1. **API is the Contract Owner** - The backend API defines the contract
2. **Dashboard is the Consumer** - The dashboard consumes the API contract
3. **No Manual DTO Duplication** - Types must be generated from OpenAPI schema
4. **Breaking Changes Require Version Bump** - All breaking changes must update the API version

## API Versioning

| Version | Base Path | Status | Notes |
|---------|-----------|--------|-------|
| v1.0 | `/api/v1` | Active | Current stable version |
| v2.0 | `/api/v2` | Planned | Future version |

### Versioning Strategy

- URL path prefixing: `/api/v1/...`, `/api/v2/...`
- Breaking changes only in new major versions
- Non-breaking changes (new fields, new endpoints) don't require version bump

### Breaking Changes

The following are considered breaking changes:

- Removing an endpoint
- Removing a field from a response
- Changing a field's type
- Changing required parameters
- Changing authentication requirements

### Non-Breaking Changes

The following are NOT considered breaking changes:

- Adding new optional fields
- Adding new endpoints
- Adding new enum values

## Dashboard Compatibility

The dashboard declares its supported API contract version at build time via `VITE_API_CONTRACT_VERSION`. This version is baked into the build artifact during the Docker build or npm build process.

### Build-Time Version Declaration

The API contract version is:

1. **Read from** `docs/api-contract/v1.0.md` (the version in the header, e.g., `# API Contract v1.0`)
2. **Injected into** the dashboard build via `VITE_API_CONTRACT_VERSION`
3. **Displayed in** the dashboard footer alongside other build metadata

### Version Correlation

| Dashboard Build | API Contract | Expected Behavior |
|-----------------|--------------|------------------|
| v1.0 (v1.0) | v1.0 | ✅ Fully compatible |
| v1.0 (v1.0) | v1.1 | ⚠️ Minor version - backward compatible |
| v1.0 (v1.0) | v2.0 | ❌ Breaking change - upgrade required |

### Verifying Version Alignment

Operators can verify version alignment by:

1. **Dashboard footer** - Shows the API contract version the dashboard was built against
2. **API `/health` endpoint** - Returns API version information
3. **Docker container inspection** - Build metadata is embedded in the container

## Schema

The OpenAPI schema is auto-generated from FastAPI:

- **Development:** `http://localhost:8001/api/openapi.json`
- **Production:** Available at the same path on deployed API

## Type Generation

The dashboard uses `openapi-typescript` to generate TypeScript types from the OpenAPI schema:

```bash
# Generate types from schema
npm run generate-types

# Validate contract and types
npm run validate-contract
```

## CI/CD Validation

The build process validates the API contract:

1. **Schema Generation** - FastAPI auto-generates OpenAPI schema
2. **Type Generation** - Dashboard generates TypeScript types
3. **Build Validation** - Build fails if types are outdated or schema is invalid

See `.github/workflows/validate-contract.yml` for CI configuration.

## Migration Guide

When updating the API contract:

1. Update the OpenAPI schema in FastAPI
2. Run type generation in the dashboard
3. Update dashboard code if needed
4. Update this migration guide

### v1.0.0 → v2.0.0 (Planned)

_Changes to be documented when v2.0 is released._

## Endpoint Reference

### Core Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API root information |
| GET | `/health` | Health check |
| GET | `/api/v1/status` | System status |
| GET | `/api/v1/stats` | Statistics |
| GET | `/api/v1/documents/status` | Document status counts |
| GET | `/api/v1/jobs/status` | Job status counts |
| GET | `/api/v1/jobs` | List jobs |
| GET | `/api/v1/operations/documents` | List documents |
| GET | `/api/v1/operations/documents/{id}/journey` | Document journey |
| GET | `/api/v1/operations/documents/{id}/extractions` | Document extractions |
| GET | `/api/v1/timeline` | Event timeline |

### Question/Answer Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/collections/{id}/questions` | Ask question |
| GET | `/api/v1/questions/{id}` | Get question status |
| GET | `/api/v1/questions/{id}/answer` | Get answer |
| GET | `/api/v1/questions/{id}/evidence` | Get evidence |

## Response Format

All responses follow a consistent format:

```typescript
interface ApiResponse<T> {
  data?: T
  error?: {
    code: string
    message: string
    details?: Array<{
      field: string
      message: string
    }>
    request_id?: string
  }
  pagination?: {
    total: number
    limit: number
    returned: number
  }
  timestamp: string
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid request parameters |
| AUTHENTICATION_ERROR | 401 | Invalid or missing token |
| AUTHORIZATION_ERROR | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| DUPLICATE_ERROR | 409 | Resource already exists |
| RATE_LIMIT_ERROR | 429 | Too many requests |
| TIMEOUT_ERROR | 504 | Operation timed out |
| INTERNAL_ERROR | 500 | Unexpected server error |
