# Design: Consolidate to PostgreSQL

## Context

A2rchi currently uses three separate database systems:
- **PostgreSQL**: Conversations, feedback, timing, configs (with 73K+ duplicate rows)
- **ChromaDB**: Vector embeddings for document chunks
- **SQLite** (catalog.sqlite): Document catalog and metadata

This architecture adds operational complexity, memory overhead, and makes backup/restore difficult.

### Constraints
- Must maintain data integrity during migration
- Embedding dimensions are fixed per model (changing requires full re-index)
- pg_textsearch requires PostgreSQL 17+ (GA expected Feb 2026)
- Brief downtime acceptable for migration (not zero-downtime)

### Stakeholders
- Operators: Need simpler deployment and backup
- Users: Need runtime config changes without restart
- Developers: Need cleaner data access patterns

## Goals / Non-Goals

### Goals
- Single PostgreSQL database for all persistent state
- Static vs dynamic config separation
- Runtime-modifiable settings via UI
- BYOK API key storage with encryption
- 3-tier document selection (system → user → conversation)
- True BM25 ranking via pg_textsearch

### Non-Goals
- Zero-downtime migration (brief cutover acceptable)
- Backward compatibility with ChromaDB (full migration required)
- Multi-tenant / multi-deployment support (single deployment focus)

## Key Decisions

### 1. PostgreSQL Extensions
| Extension | Purpose |
|-----------|---------|
| `pgvector` | Vector similarity search (HNSW/IVFFlat indexes) |
| `pg_textsearch` | BM25 full-text ranking (Timescale) |
| `pgcrypto` | API key encryption at rest |
| `pg_trgm` | Fuzzy name matching for document search |

**Rationale**: All extensions are well-maintained and available in PostgreSQL ecosystem. pg_textsearch provides true BM25 (vs ts_rank which lacks IDF weighting).

### 2. Vector Index Strategy
Default to **HNSW** index:
- No training data required (unlike IVFFlat)
- Good balance of speed and accuracy
- Configurable `m` and `ef_construction` parameters

**Alternative considered**: IVFFlat - faster for very large datasets but requires `CREATE INDEX` after data load.

### 3. Config Split: Static vs Dynamic

**Static** (set at deploy time, stored in `static_config` table):
- deployment_name, data_path
- embedding_model, embedding_dimensions
- chunk_size, chunk_overlap
- available_pipelines, available_models
- auth configuration

**Dynamic** (runtime-modifiable, stored in `dynamic_config` table):
- active_pipeline, active_model
- temperature, max_tokens, system_prompt
- num_documents_to_retrieve
- hybrid search weights

**Rationale**: Changing embedding model invalidates all vectors. Changing model selection is a common runtime operation.

### 4. BYOK Key Encryption
- Use `pgp_sym_encrypt()` / `pgp_sym_decrypt()` from pgcrypto
- Encryption key from `BYOK_ENCRYPTION_KEY` environment variable
- Keys stored encrypted in `users` table columns

**Alternative considered**: Application-level encryption - rejected because pgcrypto is simpler and keeps encryption in database layer.

### 5. Hybrid Search Algorithm
```
combined_score = (semantic_score × 0.7) + (normalized_bm25_score × 0.3)
```

- Semantic score: `1 - cosine_distance` (already [0,1])
- BM25 score: pg_textsearch `<@>` operator returns negative scores, negated and normalized
- Weights configurable in dynamic_config

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| pg_textsearch not yet GA | Monitor Timescale releases; fall back to ts_rank if needed |
| Migration downtime | Document expected times; provide pre-migration checklist |
| pgvector performance at scale | Benchmarked at 1.25-1.54x overhead (acceptable) |
| Embedding dimension change | Document as breaking change requiring full re-index |

## Migration Plan

### Pre-Migration
1. Backup existing PostgreSQL, ChromaDB, SQLite data
2. Verify PostgreSQL 17 compatibility
3. Test migration script on staging environment

### Migration Steps
1. Stop A2rchi services (downtime begins)
2. Deploy new PostgreSQL 17 container with extensions
3. Run schema creation (init.sql)
4. Migrate catalog.sqlite → documents table
5. Migrate/re-embed documents → document_chunks
6. Migrate conversation data (add model_used columns)
7. Initialize static_config from config.yaml
8. Initialize dynamic_config with defaults
9. Start A2rchi services (downtime ends)

### Rollback
- Keep original PostgreSQL 16 data volume
- Keep ChromaDB data volume
- Rollback = restore volumes and restart old containers

## Open Questions

All resolved - see proposal.md "Review: Risks, Gaps, and Uncertainties" section.
