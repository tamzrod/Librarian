# Librarian REST API Specification

**Version:** 1.0.0  
**Base URL:** `/api/v1`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Patterns](#common-patterns)
4. [Collections](#collections)
5. [Documents](#documents)
6. [Entities](#entities)
7. [Events](#events)
8. [Locations](#locations)
9. [Relationships](#relationships)
10. [Questions](#questions)
11. [Error Handling](#error-handling)
12. [Versioning](#versioning)

---

## Overview

Librarian is a context reconstruction engine for bounded file collections. This API provides programmatic access to:

- Collection management
- Document indexing and search
- Entity extraction and retrieval
- Event timeline construction
- Location tracking
- Relationship mapping
- Natural language question answering

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Response Format | JSON | Universal compatibility |
| Date Format | ISO 8601 (`YYYY-MM-DDTHH:mm:ssZ`) | Standard interchange format |
| Pagination | Cursor-based | Efficient for large datasets |
| Encoding | UTF-8 | Support for international text |
| Compression | gzip (optional) | Bandwidth optimization |

---

## Authentication

All endpoints require authentication via Bearer token.

```http
Authorization: Bearer <token>
```

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Bearer token |
| `Content-Type` | Yes (POST/PUT) | `application/json` |
| `Accept` | No | `application/json` (default) |
| `Accept-Encoding` | No | `gzip` for compression |

---

## Common Patterns

### Request ID

Every request should include an idempotency key for tracing:

```http
X-Request-ID: <uuid>
```

### Pagination

All list endpoints support cursor-based pagination:

**Request:**
```
GET /collections/{id}/documents?limit=20&cursor=eyJsYXN0X2lkIjogMTIzfQ
```

**Response Headers:**
```
X-Total-Count: 150
X-Has-More: true
X-Cursor: eyJsYXN0X2lkIjogMTQ5fQ
```

**Response Body:**
```json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "limit": 20,
    "has_more": true,
    "next_cursor": "eyJsYXN0X2lkIjogMTQ5fQ"
  }
}
```

### Filtering

Filter parameters use a consistent query syntax:

```
GET /documents?filter[extension]=pdf&filter[modified_after]=2026-01-01
```

| Operator | Syntax | Example |
|----------|--------|---------|
| Equals | `filter[field]=value` | `filter[extension]=pdf` |
| Contains | `filter[field][contains]=value` | `filter[path][contains]=contract` |
| Greater Than | `filter[field][gt]=value` | `filter[size][gt]=1000` |
| Less Than | `filter[field][lt]=value` | `filter[size][lt]=10000` |
| In List | `filter[field][in]=a,b,c` | `filter[type][in]=person,org` |
| Not Null | `filter[field][exists]=true` | `filter[latitude][exists]=true` |

### Sorting

```
GET /documents?sort=modified_time:desc,name:asc
```

---

## Collections

A **Collection** represents a bounded set of files being indexed.

### URI Layout

```
/collections
/collections/{collection_id}
```

### Endpoints

#### List Collections

```http
GET /collections
```

**Response: 200 OK**
```json
{
  "data": [
    {
      "id": 1,
      "name": "Work Documents",
      "root_path": "/home/user/documents",
      "document_count": 150,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-06-15T10:30:00Z"
    }
  ],
  "pagination": {
    "total": 3,
    "limit": 20,
    "has_more": false
  }
}
```

#### Create Collection

```http
POST /collections
```

**Request Body:**
```json
{
  "name": "Work Documents",
  "root_path": "/home/user/documents"
}
```

**Response: 201 Created**
```json
{
  "id": 1,
  "name": "Work Documents",
  "root_path": "/home/user/documents",
  "document_count": 0,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

#### Get Collection

```http
GET /collections/{collection_id}
```

**Response: 200 OK**
```json
{
  "id": 1,
  "name": "Work Documents",
  "root_path": "/home/user/documents",
  "document_count": 150,
  "entity_count": 423,
  "event_count": 89,
  "location_count": 34,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-06-15T10:30:00Z"
}
```

#### Delete Collection

```http
DELETE /collections/{collection_id}
```

**Response: 204 No Content**

---

## Documents

A **Document** represents an indexed file.

### URI Layout

```
/collections/{collection_id}/documents
/collections/{collection_id}/documents/{document_id}
/documents/{document_id}/entities
/documents/{document_id}/events
/documents/{document_id}/locations
```

### Endpoints

#### List Documents

```http
GET /collections/{collection_id}/documents
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | int | Max results (default: 20, max: 100) |
| `cursor` | string | Pagination cursor |
| `filter[extension]` | string | File extension filter |
| `filter[modified_after]` | date | Modified after date |
| `filter[modified_before]` | date | Modified before date |
| `filter[path_contains]` | string | Path contains substring |
| `q` | string | Full-text search query |
| `sort` | string | Sort field and direction |

**Response: 200 OK**
```json
{
  "data": [
    {
      "id": 42,
      "collection_id": 1,
      "path": "/home/user/documents/contracts/abc_contract.pdf",
      "extension": ".pdf",
      "sha256": "a3f5d...",
      "file_size": 245678,
      "character_count": 12345,
      "modified_time": "2026-03-15T14:22:00Z",
      "indexed_at": "2026-06-01T08:00:00Z",
      "parser": "pdf_parser"
    }
  ],
  "pagination": {
    "total": 150,
    "limit": 20,
    "has_more": true,
    "next_cursor": "eyJpZCI6IDYyfQ"
  }
}
```

#### Get Document

```http
GET /collections/{collection_id}/documents/{document_id}
```

**Response: 200 OK**
```json
{
  "id": 42,
  "collection_id": 1,
  "path": "/home/user/documents/contracts/abc_contract.pdf",
  "extension": ".pdf",
  "sha256": "a3f5d...",
  "file_size": 245678,
  "character_count": 12345,
  "modified_time": "2026-03-15T14:22:00Z",
  "indexed_at": "2026-06-01T08:00:00Z",
  "parser": "pdf_parser",
  "text_preview": "This Agreement is entered into by and between ABC Corp...",
  "entities": [
    {"id": 1, "type": "organization", "value": "ABC Corp"},
    {"id": 2, "type": "person", "value": "John Smith"}
  ],
  "events": [
    {"id": 5, "timestamp": "2026-03-15", "event_type": "signature", "description": "Contract signed"}
  ],
  "locations": [
    {"id": 3, "name": "Manila", "latitude": 14.5995, "longitude": 120.9842}
  ]
}
```

#### Search Documents

```http
GET /documents/search
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | **Required.** Search query |
| `collection_id` | int | Filter by collection |
| `limit` | int | Max results |
| `include_text` | bool | Include text snippets |

**Response: 200 OK**
```json
{
  "data": [
    {
      "id": 42,
      "path": "/home/user/documents/contracts/abc_contract.pdf",
      "score": 0.95,
      "snippets": [
        "ABC Corp located in <mark>Manila</mark>",
        "Signed by <mark>John Smith</mark> on 2026-03-15"
      ]
    }
  ],
  "query": "ABC Corp Manila",
  "total_results": 5
}
```

---

## Entities

An **Entity** is a named thing extracted from documents.

### URI Layout

```
/collections/{collection_id}/entities
/entities/{entity_id}
/entities/{entity_id}/documents
```

### Endpoints

#### List Entities

```http
GET /collections/{collection_id}/entities
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `filter[type]` | string | Entity type (person, organization, device, location) |
| `filter[value_contains]` | string | Value contains substring |
| `min_occurrences` | int | Minimum occurrence count |

**Response: 200 OK**
```json
{
  "data": [
    {
      "id": 1,
      "type": "organization",
      "value": "ABC Corp",
      "normalized_value": "abc corp",
      "document_count": 5,
      "sources": ["contracts/abc_contract.pdf", "invoices/abc_invoice.pdf"]
    },
    {
      "id": 2,
      "type": "person",
      "value": "John Smith",
      "normalized_value": "john smith",
      "document_count": 12,
      "sources": ["contracts/abc_contract.pdf", "meeting_notes/2026-03.md"]
    }
  ],
  "pagination": {
    "total": 423,
    "limit": 20,
    "has_more": true
  }
}
```

#### Get Entity

```http
GET /entities/{entity_id}
```

**Response: 200 OK**
```json
{
  "id": 1,
  "type": "organization",
  "value": "ABC Corp",
  "normalized_value": "abc corp",
  "document_count": 5,
  "relationships": [
    {
      "id": 10,
      "to_entity_id": 5,
      "to_entity_value": "Manila",
      "relationship_type": "located_in",
      "source": "contracts/abc_contract.pdf"
    },
    {
      "id": 11,
      "to_entity_id": 2,
      "to_entity_value": "John Smith",
      "relationship_type": "employs",
      "source": "contracts/abc_contract.pdf"
    }
  ]
}
```

---

## Events

An **Event** is a timestamped occurrence extracted from documents.

### URI Layout

```
/collections/{collection_id}/events
/events/{event_id}
/events/{event_id}/documents
```

### Endpoints

#### List Events

```http
GET /collections/{collection_id}/events
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `filter[event_type]` | string | Event type (photo, site_visit, signature, etc.) |
| `filter[date_after]` | date | Events after date |
| `filter[date_before]` | date | Events before date |
| `filter[month]` | string | Events in month (YYYY-MM) |
| `sort` | string | Sort by timestamp (default: desc) |

**Response: 200 OK**
```json
{
  "data": [
    {
      "id": 5,
      "timestamp": "2026-03-15T10:00:00Z",
      "event_type": "signature",
      "description": "Contract signed by ABC Corp",
      "document_count": 1,
      "sources": ["contracts/abc_contract.pdf"]
    },
    {
      "id": 8,
      "timestamp": "2026-01-15T09:30:00Z",
      "event_type": "site_visit",
      "description": "Site inspection at Marikina facility",
      "document_count": 2,
      "sources": ["meeting_notes/2026-01.md", "photos/IMG_20260115.jpg"]
    }
  ],
  "pagination": {
    "total": 89,
    "limit": 20,
    "has_more": true
  }
}
```

#### Get Event

```http
GET /events/{event_id}
```

**Response: 200 OK**
```json
{
  "id": 8,
  "timestamp": "2026-01-15T09:30:00Z",
  "event_type": "site_visit",
  "description": "Site inspection at Marikina facility",
  "related_locations": [
    {"id": 3, "name": "Marikina", "latitude": 14.6389, "longitude": 121.1156}
  ],
  "related_entities": [
    {"id": 1, "type": "organization", "value": "ABC Corp"},
    {"id": 2, "type": "person", "value": "John Smith"}
  ],
  "documents": [
    {"id": 15, "path": "meeting_notes/2026-01.md"},
    {"id": 22, "path": "photos/IMG_20260115.jpg"}
  ]
}
```

---

## Locations

A **Location** is a geographic point extracted from documents.

### URI Layout

```
/collections/{collection_id}/locations
/locations/{location_id}
/locations/{location_id}/documents
```

### Endpoints

#### List Locations

```http
GET /collections/{collection_id}/locations
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `filter[name_contains]` | string | Location name contains |
| `filter[has_coordinates]` | bool | Has GPS coordinates |
| `filter[date]` | date | Locations from specific date |

**Response: 200 OK**
```json
{
  "data": [
    {
      "id": 3,
      "name": "Manila",
      "latitude": 14.5995,
      "longitude": 120.9842,
      "coordinate_source": "gps_exif",
      "document_count": 8,
      "first_seen": "2026-01-01T12:00:00Z",
      "last_seen": "2026-06-15T10:30:00Z"
    },
    {
      "id": 4,
      "name": "Marikina",
      "latitude": 14.6389,
      "longitude": 121.1156,
      "coordinate_source": "text_extraction",
      "document_count": 5,
      "first_seen": "2026-01-15T09:30:00Z",
      "last_seen": "2026-06-10T14:00:00Z"
    }
  ],
  "pagination": {
    "total": 34,
    "limit": 20,
    "has_more": false
  }
}
```

#### Get Location

```http
GET /locations/{location_id}
```

**Response: 200 OK**
```json
{
  "id": 3,
  "name": "Manila",
  "latitude": 14.5995,
  "longitude": 120.9842,
  "coordinate_source": "gps_exif",
  "document_count": 8,
  "related_entities": [
    {"id": 1, "type": "organization", "value": "ABC Corp", "relationship": "located_in"}
  ],
  "timeline": [
    {"timestamp": "2026-01-01", "event_type": "photo", "description": "Photo taken"},
    {"timestamp": "2026-03-15", "event_type": "signature", "description": "Contract signed"}
  ]
}
```

---

## Relationships

A **Relationship** connects two entities.

### URI Layout

```
/collections/{collection_id}/relationships
/relationships/{relationship_id}
/entities/{entity_id}/relationships
```

### Endpoints

#### List Relationships

```http
GET /collections/{collection_id}/relationships
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `filter[type]` | string | Relationship type (located_in, works_for, etc.) |
| `filter[from_entity]` | string | From entity value |
| `filter[to_entity]` | string | To entity value |

**Response: 200 OK**
```json
{
  "data": [
    {
      "id": 10,
      "from_entity": {
        "id": 1,
        "type": "organization",
        "value": "ABC Corp"
      },
      "to_entity": {
        "id": 3,
        "type": "location",
        "value": "Manila"
      },
      "relationship_type": "located_in",
      "confidence": 0.95,
      "source": "contracts/abc_contract.pdf"
    },
    {
      "id": 11,
      "from_entity": {
        "id": 2,
        "type": "person",
        "value": "John Smith"
      },
      "to_entity": {
        "id": 1,
        "type": "organization",
        "value": "ABC Corp"
      },
      "relationship_type": "works_for",
      "confidence": 0.90,
      "source": "contracts/abc_contract.pdf"
    }
  ],
  "pagination": {
    "total": 156,
    "limit": 20,
    "has_more": true
  }
}
```

---

## Questions

Question answering endpoint for natural language queries against the collection.

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Processing Mode | **Synchronous** (default), Async available | Simpler for most use cases; async for long queries |
| Response Content | **Answer + Evidence** (configurable) | Full transparency for verification |
| Timeout | 30 seconds sync, 5 minutes async | Prevent runaway queries |
| Caching | Yes, 1 hour TTL | Reduce repeated query load |

### URI Layout

```
/collections/{collection_id}/questions
/questions/{question_id}        # For async status
/questions/{question_id}/answer
/questions/{question_id}/evidence
```

### Endpoints

#### Ask Question (Synchronous)

```http
POST /collections/{collection_id}/questions
```

**Request Body:**
```json
{
  "question": "Where was the site visit on January 15, 2026?",
  "options": {
    "include_evidence": true,
    "max_evidence_items": 10,
    "evidence_types": ["events", "locations", "documents"],
    "confidence_threshold": 0.5
  }
}
```

**Response: 200 OK**
```json
{
  "id": "q-abc123",
  "question": "Where was the site visit on January 15, 2026?",
  "status": "completed",
  "answer": {
    "text": "The site visit on January 15, 2026 took place at the Marikina facility.",
    "confidence": 0.92,
    "intent": "location_query"
  },
  "evidence": {
    "events": [
      {
        "id": 8,
        "timestamp": "2026-01-15T09:30:00Z",
        "event_type": "site_visit",
        "description": "Site inspection at Marikina facility",
        "score": 100,
        "source": "meeting_notes/2026-01.md"
      }
    ],
    "locations": [
      {
        "id": 4,
        "name": "Marikina",
        "latitude": 14.6389,
        "longitude": 121.1156,
        "score": 100,
        "source": "meeting_notes/2026-01.md"
      }
    ],
    "documents": [
      {
        "id": 15,
        "path": "meeting_notes/2026-01.md",
        "score": 80,
        "source": "meeting_notes/2026-01.md"
      }
    ],
    "trace": [
      {
        "type": "event",
        "source": "meeting_notes/2026-01.md",
        "score": 100,
        "reason": "exif_timestamp"
      },
      {
        "type": "location",
        "source": "meeting_notes/2026-01.md",
        "score": 100,
        "reason": "gps_exif"
      }
    ]
  },
  "created_at": "2026-06-28T14:30:00Z",
  "completed_at": "2026-06-28T14:30:01Z"
}
```

#### Ask Question (Asynchronous)

For long-running queries, request async processing:

```http
POST /collections/{collection_id}/questions
```

**Request Body:**
```json
{
  "question": "Summarize all contract renewals over the past year",
  "async": true
}
```

**Response: 202 Accepted**
```json
{
  "id": "q-def456",
  "question": "Summarize all contract renewals over the past year",
  "status": "pending",
  "poll_url": "/questions/q-def456",
  "created_at": "2026-06-28T14:30:00Z"
}
```

#### Get Question Status

```http
GET /questions/{question_id}
```

**Response (Pending):**
```json
{
  "id": "q-def456",
  "status": "processing",
  "progress": 0.45,
  "created_at": "2026-06-28T14:30:00Z"
}
```

**Response (Completed):**
```json
{
  "id": "q-def456",
  "status": "completed",
  "answer": {
    "text": "There were 5 contract renewals in the past year...",
    "confidence": 0.88
  },
  "completed_at": "2026-06-28T14:32:15Z"
}
```

#### Get Answer Only

```http
GET /questions/{question_id}/answer
```

**Response: 200 OK**
```json
{
  "id": "q-abc123",
  "question": "Where was the site visit on January 15, 2026?",
  "answer": {
    "text": "The site visit on January 15, 2026 took place at the Marikina facility.",
    "confidence": 0.92
  }
}
```

#### Get Evidence Only

```http
GET /questions/{question_id}/evidence
```

**Response: 200 OK**
```json
{
  "id": "q-abc123",
  "evidence": {
    "events": [...],
    "locations": [...],
    "documents": [...],
    "trace": [...]
  },
  "score_breakdown": [
    {"type": "event", "item": "site_visit", "score": 100, "reason": "exif_timestamp"},
    {"type": "location", "item": "Marikina", "score": 100, "reason": "gps_exif"}
  ]
}
```

#### List Questions

```http
GET /collections/{collection_id}/questions
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `filter[status]` | string | pending, processing, completed, failed |
| `filter[date_after]` | date | Questions after date |

**Response: 200 OK**
```json
{
  "data": [
    {
      "id": "q-abc123",
      "question": "Where was the site visit on January 15, 2026?",
      "status": "completed",
      "confidence": 0.92,
      "created_at": "2026-06-28T14:30:00Z"
    }
  ],
  "pagination": {...}
}
```

---

## Error Handling

### Error Response Format

All errors follow a consistent structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid filter parameter",
    "details": [
      {
        "field": "filter[date_after]",
        "message": "Invalid date format. Expected YYYY-MM-DD"
      }
    ],
    "request_id": "req-xyz789"
  }
}
```

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET, PUT |
| 201 | Created | Successful POST |
| 202 | Accepted | Async operation started |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource |
| 422 | Unprocessable | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Error | Server error |
| 503 | Service Unavailable | Maintenance or overload |

### Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Request parameters invalid |
| `AUTHENTICATION_ERROR` | Invalid or missing token |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `DUPLICATE_ERROR` | Resource already exists |
| `RATE_LIMIT_ERROR` | Too many requests |
| `TIMEOUT_ERROR` | Operation timed out |
| `INTERNAL_ERROR` | Unexpected server error |

---

## Versioning

### Strategy

API versioning uses URL path prefixing:

```
/api/v1/...
/api/v2/...  (future)
```

### Version Negotiation

Clients can specify minimum version:

```http
Accept: application/json; version=1.0
```

### Breaking Changes

Breaking changes will only occur in new major versions:

| Change Type | Requires New Version |
|-------------|---------------------|
| Remove endpoint | Yes |
| Remove field | Yes |
| Change field type | Yes |
| Add optional field | No |
| Add new endpoint | No |
| Add new enum value | No |

### Deprecation

Deprecated features will include headers:

```http
Deprecation: true
Sunset: Sat, 31 Dec 2027 23:59:59 GMT
Link: <https://docs.librarian.io/api/v2>; rel="successor-version"
```

---

## Example Flows

### Flow 1: Index a New Collection

```bash
# 1. Create collection
curl -X POST /api/v1/collections \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Work Docs", "root_path": "/home/user/docs"}'

# Response: {"id": 1, ...}

# 2. Start indexing (background job)
curl -X POST /api/v1/collections/1/index \
  -H "Authorization: Bearer $TOKEN"

# 3. Poll for status
curl /api/v1/collections/1 \
  -H "Authorization: Bearer $TOKEN"

# Response: {"status": "indexing", "progress": 0.45, ...}
```

### Flow 2: Ask a Question

```bash
# 1. Ask question
curl -X POST /api/v1/collections/1/questions \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"question": "When was the contract signed?"}'

# Response: {"id": "q-123", "status": "completed", "answer": {...}, "evidence": {...}}
```

### Flow 3: Explore Entity Relationships

```bash
# 1. Find entity
curl "/api/v1/collections/1/entities?filter[value_contains]=ABC" \
  -H "Authorization: Bearer $TOKEN"

# 2. Get entity details with relationships
curl /api/v1/entities/1 \
  -H "Authorization: Bearer $TOKEN"

# 3. Get related documents
curl /api/v1/entities/1/documents \
  -H "Authorization: Bearer $TOKEN"
```

---

## Rate Limits

| Tier | Requests/minute | Burst |
|------|-----------------|-------|
| Free | 60 | 10 |
| Pro | 600 | 100 |
| Enterprise | 6000 | 1000 |

Rate limit headers:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1719584400
```

---

## SDK Support

Official SDKs will be provided for:

- Python (`pip install librarian-sdk`)
- JavaScript/TypeScript (`npm install librarian-sdk`)
- Go (`go get github.com/librarian/sdk-go`)

SDK documentation: https://docs.librarian.io/sdk