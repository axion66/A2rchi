# Spec Review: Gaps, Issues, and Risks

## 🔴 Critical Gaps (Must Address)

### 1. Missing LangChain VectorStore Interface Compatibility
**Gap**: The `PostgresVectorStore` spec doesn't mention LangChain interface compatibility.

**Current code** uses LangChain's `VectorStore` interface:
```python
# src/data_manager/vectorstore/retrievers/grading_retriever.py
from langchain_core.vectorstores.base import VectorStore
```

**Risk**: If `PostgresVectorStore` doesn't implement the LangChain `VectorStore` interface, all retrievers break.

**Recommendation**: Add scenario:
```markdown
#### Scenario: LangChain VectorStore interface
- **WHEN** PostgresVectorStore is instantiated
- **THEN** it implements langchain_core.vectorstores.base.VectorStore
- **AND** similarity_search_with_score() returns List[Tuple[Document, float]]
```

---

### 2. Missing Embedding Model Initialization
**Gap**: No spec for how the embedding model is loaded and used by PostgresVectorStore.

**Current code** (manager.py lines 44-50):
```python
embedding_class_map = self._data_manager_config["embedding_class_map"]
embedding_entry = embedding_class_map[embedding_name]
embedding_class = embedding_entry["class"]
self.embedding_model = embedding_class(**embedding_kwargs)
```

**Risk**: PostgresVectorStore needs access to embedding model to embed queries.

**Recommendation**: Add to PostgresVectorStore spec:
```markdown
#### Scenario: Query embedding
- **WHEN** similarity_search(query_text, k) is called
- **THEN** query_text is embedded using the configured embedding model
- **AND** the resulting vector is used for similarity search
```

---

### 3. Missing Connection Pool / Session Management
**Gap**: No spec for database connection management.

**Risk**: Without connection pooling, each request creates a new connection → performance degradation and connection exhaustion.

**Recommendation**: Add requirement to database/spec.md:
```markdown
### Requirement: Connection Pool Management
The system SHALL use a connection pool for PostgreSQL connections.

#### Scenario: Connection reuse
- **WHEN** multiple requests need database access
- **THEN** connections are reused from a pool
- **AND** pool size is configurable (default: 5-20)
```

---

### 4. Missing Transaction Semantics for Migration
**Gap**: The migration spec says "transaction is rolled back" but doesn't specify transaction boundaries.

**Risk**: If re-embedding 10K documents takes 2 hours, a single transaction would hold locks too long and likely fail.

**Recommendation**: Clarify migration transaction strategy:
```markdown
#### Scenario: Chunked migration with checkpoints
- **WHEN** migrating large datasets (>1000 documents)
- **THEN** migration proceeds in batches (e.g., 100 documents)
- **AND** progress is checkpointed after each batch
- **AND** failed migration can resume from last checkpoint
```

---

## 🟡 Medium Issues (Should Address)

### 5. No Delete Documents from VectorStore Scenario
**Gap**: PostgresVectorStore has no scenario for deleting/removing documents.

**Current code** (manager.py) likely has delete logic for re-sync.

**Recommendation**: Add scenario:
```markdown
#### Scenario: Delete document chunks
- **WHEN** a document is soft-deleted in the documents table
- **THEN** its chunks are excluded from search results
- **AND** chunks can be permanently deleted via cleanup job
```

---

### 6. Missing Error Scenarios
**Gap**: Most requirements don't specify error conditions.

| Requirement | Missing Error Scenario |
|-------------|------------------------|
| BYOK API key storage | Invalid encryption key, provider not supported |
| Dynamic config update | Validation errors (invalid model, temperature out of range) |
| Similarity search | Database connection failure, corrupted index |
| Migration | Insufficient disk space, permission denied |

**Recommendation**: Add ERROR scenarios to critical paths.

---

### 7. Config Caching and Invalidation Not Specified
**Gap**: Static config says "cached in memory for fast access" but no invalidation strategy.

**Risk**: If multiple services run (chat, data_manager, etc.), they may have stale caches.

**Recommendation**: Add scenario:
```markdown
#### Scenario: Dynamic config cache invalidation
- **WHEN** dynamic config is updated via API
- **THEN** in-memory cache is invalidated
- **AND** next read fetches fresh values from database
```

---

### 8. Hybrid Search Fallback Not Specified
**Gap**: What happens if BM25 index is unavailable (pg_textsearch not installed)?

**Risk**: pg_textsearch requires PostgreSQL 17+ and isn't GA yet. Need graceful degradation.

**Recommendation**: Add scenario:
```markdown
#### Scenario: BM25 unavailable fallback
- **WHEN** pg_textsearch extension is not available
- **THEN** hybrid search falls back to semantic-only search
- **AND** a warning is logged indicating BM25 is disabled
```

---

### 9. Anonymous User Handling Unclear
**Gap**: Users table has `auth_provider = 'anonymous'` but spec doesn't clarify how anonymous users get IDs.

**Current behavior**: Likely uses client_id from cookies/session.

**Recommendation**: Add scenario:
```markdown
#### Scenario: Anonymous user identification
- **WHEN** an unauthenticated user interacts with the system
- **THEN** a user_id is generated from client session/cookie
- **AND** auth_provider is set to 'anonymous'
- **AND** the user can later be upgraded to authenticated
```

---

## 🟢 Minor Issues (Nice to Have)

### 10. No Bulk Operations Specified
**Gap**: Document selection API only shows single-document operations.

**Recommendation**: Add scenario:
```markdown
#### Scenario: Bulk update document defaults
- **WHEN** PUT /api/user/document-defaults is called with array of doc_ids
- **THEN** all specified documents are updated in one transaction
```

---

### 11. No Pagination for Document Listings
**Gap**: `GET /api/user/document-defaults` doesn't specify pagination.

**Risk**: Large deployments with 1000+ documents will have slow API responses.

---

### 12. Index Rebuild Not Specified
**Gap**: No spec for rebuilding HNSW/BM25 indexes if they become corrupted or need tuning.

---

### 13. Migration --dry-run Not Specified
**Gap**: No scenario for previewing migration without executing.

---

## 🔵 Risks to Monitor

### R1: pg_textsearch GA Timeline
- Currently pre-GA, expected Feb 2026
- Mitigation: Fallback to semantic-only is specified

### R2: PostgreSQL 17 Adoption
- Some hosting providers may not support PG17 yet
- Mitigation: Document hosting requirements clearly

### R3: Vector Dimension Lock-in
- Changing embedding model requires full re-index
- Mitigation: Documented as breaking change; migration script handles re-embedding

### R4: Migration Data Loss
- SQLite/ChromaDB may have data not mapped to new schema
- Mitigation: Preserve extra_json field for unmapped metadata

### R5: Performance Regression
- Hybrid search adds overhead (two index lookups + normalization)
- Mitigation: Benchmarks show acceptable overhead; weights are tunable

---

## Summary

| Category | Count | Action |
|----------|-------|--------|
| 🔴 Critical | 4 | Must fix before implementation |
| 🟡 Medium | 5 | Should address during implementation |
| 🟢 Minor | 4 | Nice to have |
| 🔵 Risks | 5 | Monitor |
