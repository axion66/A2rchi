# Proposal: Consolidate Storage to PostgreSQL with pgvector

## Summary

Replace ChromaDB and SQLite catalog with PostgreSQL + pgvector extension, consolidating all data storage into a single database service.

## Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      A2rchi Backend                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   │
│  │ PostgreSQL  │   │  ChromaDB   │   │ SQLite Catalog  │   │
│  │             │   │             │   │ (catalog.sqlite)│   │
│  ├─────────────┤   ├─────────────┤   ├─────────────────┤   │
│  │ • Chats     │   │ • Embeddings│   │ • Document index│   │
│  │ • Feedback  │   │ • Vectors   │   │ • Metadata      │   │
│  │ • Configs   │   │ • Metadata  │   │ • Selection     │   │
│  │ • Timing    │   │             │   │   state         │   │
│  │ • Tool calls│   │             │   │                 │   │
│  └─────────────┘   └─────────────┘   └─────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Problems:**
1. Three separate storage systems to maintain
2. ChromaDB adds container complexity and memory overhead
3. SQLite file-based storage complicates backups and scaling
4. No transactional consistency across stores
5. Complex deployment with multiple services

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      A2rchi Backend                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              PostgreSQL + pgvector                   │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ • Chats, Feedback, Configs, Timing, Tool calls      │   │
│  │ • Document catalog (resources table)                 │   │
│  │ • Document embeddings (vectors table with pgvector)  │   │
│  │ • Per-chat selection state                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Benefits:**
1. Single database service - simpler deployment
2. ACID transactions across all data
3. Unified backup/restore strategy
4. Better query capabilities (SQL + vector similarity)
5. Reduced memory footprint (no separate ChromaDB process)
6. Native PostgreSQL tooling (pg_dump, replication, etc.)

## Scope

### In Scope
- Add pgvector extension to PostgreSQL
- Create new tables: `documents`, `document_embeddings`, `document_selections`
- Implement `PostgresVectorStore` class replacing ChromaDB client
- Migrate `CatalogService` from SQLite to PostgreSQL
- Update `VectorStoreManager` to use PostgreSQL
- Update docker-compose to remove ChromaDB service
- Migration script for existing deployments
- Update configuration schema

### Out of Scope
- Changing embedding models or chunking strategies
- Modifying retrieval algorithms (hybrid search stays the same)
- UI changes (data viewer will work unchanged)
- Changes to chat history schema (already in PostgreSQL)

## Technical Design

### New Database Schema

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Document catalog (replaces SQLite catalog)
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    resource_hash VARCHAR(64) UNIQUE NOT NULL,
    path TEXT NOT NULL,
    display_name TEXT NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- 'local_files', 'web', 'ticket'
    url TEXT,
    ticket_id TEXT,
    suffix VARCHAR(20),
    size_bytes BIGINT,
    original_path TEXT,
    base_path TEXT,
    relative_path TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    modified_at TIMESTAMP,
    ingested_at TIMESTAMP,
    content TEXT,  -- Full document content for preview
    CONSTRAINT valid_source CHECK (source_type IN ('local_files', 'web', 'ticket'))
);

CREATE INDEX idx_documents_hash ON documents(resource_hash);
CREATE INDEX idx_documents_source ON documents(source_type);
CREATE INDEX idx_documents_name ON documents(display_name);

-- Document embeddings (replaces ChromaDB)
CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(384),  -- Dimension matches embedding model
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX idx_embeddings_document ON document_embeddings(document_id);
CREATE INDEX idx_embeddings_vector ON document_embeddings 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Per-chat document selection (replaces SQLite selection_state)
CREATE TABLE document_selections (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversation_metadata(conversation_id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(conversation_id, document_id)
);

CREATE INDEX idx_selections_conversation ON document_selections(conversation_id);
```

### Key Implementation Changes

#### 1. PostgresVectorStore (new)
```python
class PostgresVectorStore:
    """Vector store implementation using PostgreSQL + pgvector."""
    
    def __init__(self, connection_config: dict, embedding_model):
        self.conn_config = connection_config
        self.embedding_model = embedding_model
    
    def add_documents(self, documents: List[Document], embeddings: List[List[float]]):
        """Insert documents and their embeddings."""
        ...
    
    def similarity_search(self, query: str, k: int = 4, filter: dict = None) -> List[Document]:
        """Perform vector similarity search with optional filtering."""
        ...
    
    def delete_by_hash(self, resource_hash: str):
        """Delete document and its embeddings by hash."""
        ...
```

#### 2. CatalogService Updates
- Replace SQLite connection with PostgreSQL
- Use existing connection pool from chat app
- Keep same public API for backward compatibility

#### 3. VectorStoreManager Updates
- Replace `_build_client()` to return `PostgresVectorStore`
- Update `_add_to_vectorstore()` and `_remove_from_vectorstore()`
- Remove ChromaDB imports and configuration handling

### Configuration Changes

```yaml
services:
  postgres:
    port: 5432
    user: a2rchi
    database: a2rchi-db
    host: postgres
    # New: enable pgvector
    extensions:
      - vector
    
  # chromadb section REMOVED
```

### Migration Strategy

1. **Phase 1: Schema Migration**
   - Add new tables to PostgreSQL
   - Run migration on container startup if tables don't exist

2. **Phase 2: Data Migration**  
   - Script to migrate SQLite catalog → PostgreSQL documents table
   - Script to re-embed and store in PostgreSQL (or migrate from ChromaDB)

3. **Phase 3: Code Deployment**
   - Deploy new code that uses PostgreSQL
   - Verify functionality

4. **Phase 4: Cleanup**
   - Remove ChromaDB container
   - Remove SQLite files

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| pgvector performance vs ChromaDB | Medium | Benchmark before/after; pgvector is mature and performant |
| Migration data loss | High | Backup before migration; test on staging first |
| Breaking existing deployments | High | Provide migration script; maintain backward compat temporarily |
| Embedding dimension mismatch | Medium | Make vector dimension configurable based on embedding model |

## Effort Estimate

| Task | Estimate |
|------|----------|
| PostgresVectorStore implementation | 4 hours |
| CatalogService PostgreSQL migration | 2 hours |
| VectorStoreManager updates | 2 hours |
| Schema and init.sql updates | 1 hour |
| Migration script | 2 hours |
| Docker compose updates | 1 hour |
| Testing and debugging | 4 hours |
| Documentation | 1 hour |
| **Total** | **~17 hours** |

## Success Criteria

1. ✅ All existing UI tests pass
2. ✅ Chat with RAG retrieval works identically
3. ✅ Data viewer shows documents and content
4. ✅ Document enable/disable per-chat works
5. ✅ Only PostgreSQL container required (ChromaDB removed)
6. ✅ Retrieval latency within 20% of current performance
7. ✅ Migration script successfully migrates test deployment

## Alternatives Considered

### Alternative 1: Keep ChromaDB, Remove SQLite
Move catalog metadata into ChromaDB's document metadata.
- **Rejected**: ChromaDB metadata querying is limited; no SQL capabilities

### Alternative 2: SQLite for Everything (sqlite-vec)
Use SQLite with sqlite-vec extension for vectors.
- **Rejected**: Single-writer limitation; not suitable for concurrent access

### Alternative 3: Keep Current Architecture
- **Rejected**: Unnecessary complexity; three storage systems is overkill

## Open Questions

1. Should we support both ChromaDB and PostgreSQL via configuration for transition period?
2. What's the target embedding dimension? (384 for MiniLM, 1536 for OpenAI)
3. Should we add full-text search (tsvector) alongside vector search?

## References

- [pgvector documentation](https://github.com/pgvector/pgvector)
- [PostgreSQL vector indexing](https://www.postgresql.org/docs/current/indexes-types.html)
- [ChromaDB migration guides](https://docs.trychroma.com/)
