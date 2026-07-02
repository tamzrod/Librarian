# E7: Embedding Storage Incomplete

**Status:** Partial  
**Severity:** Medium  
**Classification:** Partial Implementation
**Last Updated:** 2026-07-02 (Post-Implementation Audit)

## Implementation Status

### What Was Done

1. ✅ `EmbeddingGenerator` worker exists (`workers/embedding_generator.py`)
2. ✅ Handler registered in worker.py: `generate_embeddings`
3. ✅ `document_embeddings` table exists in schema
4. ✅ `save_embedding()` method exists in backend
5. ✅ Multiple embedding model support (OpenAI, sentence-transformers, TF-IDF fallback)

### What Remains

1. ❌ **Vector retrieval API** - No `get_embedding()` or `search_by_embedding()` endpoints
2. ❌ **Semantic search** - Not implemented in API layer
3. ❌ **No verification** - Integration tests not added

## Problem Statement

Embeddings are defined in the job system but:

1. **Worker exists:** `EmbeddingGenerator` worker exists
2. **Table exists:** `document_embeddings` table exists
3. **BUT:** Embeddings not consistently stored
4. **BUT:** No retrieval API for embeddings
5. **BUT:** Vector search not implemented

## Impact

- **User Impact:** Semantic search not available
- **Developer Impact:** Can't query by similarity
- **Data Impact:** Embedding work wasted

## Affected Files

| File | Issue |
|------|-------|
| `workers/embedding_generator.py` | Worker exists but may be incomplete |
| `storage/postgres_backend.py` | `save_embedding` exists, retrieval unclear |
| `storage/migrations/006_embeddings.sql` | Table exists |
| `api/routes/` | No vector search endpoint |

## Current State

```python
# storage/postgres_backend.py
def save_embedding(self, document_id: int, vector: list, model: str = 'unknown') -> bool:
    """Save embedding vector for a document."""
    # Implementation exists

def get_embedding(self, document_id: int) -> dict:
    """Get embedding for a document."""
    # Need to verify implementation
```

## Required Changes

### 1. Verify Embedding Storage

Check if `save_embedding` is being called correctly and storing to `document_embeddings`.

### 2. Implement Vector Retrieval

```python
# storage/postgres_backend.py
def search_by_embedding(self, query_vector: list, limit: int = 10) -> list:
    """Find similar documents using vector similarity."""
    # PostgreSQL with pgvector extension:
    # SELECT document_id, 1 - (embedding <=> %s) as similarity
    # FROM document_embeddings
    # ORDER BY embedding <=> %s
    # LIMIT %s
```

### 3. Add Vector Search API

```python
# api/routes/vector_search.py
@router.get("/search/semantic")
async def semantic_search(query: str, limit: int = 10):
    # 1. Embed query text
    query_embedding = embed_model.embed(query)
    
    # 2. Find similar documents
    results = backend.search_by_embedding(query_embedding, limit)
    
    # 3. Return documents with similarity scores
    return results
```

## Dependencies

- pgvector extension (PostgreSQL)
- Embedding model (OpenAI, local, etc.)

## Definition of Done

- [ ] Embeddings stored for all searchable documents
- [ ] Retrieval API returns embeddings
- [ ] Vector search endpoint exists
- [ ] Semantic search works

## Risk Assessment

- **Medium Risk:** Depends on external services
- **Impact:** Enables semantic search
- **Testing:** Test similarity search accuracy

## Effort Estimate

- **Time:** 6-10 hours
- **Complexity:** High
- **Testing:** Test search accuracy
