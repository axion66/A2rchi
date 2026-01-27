# Design: Remove ChromaDB

## Architecture Decision

### Current State
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Chatbot   │────▶│  ChromaDB   │     │  PostgreSQL │
│   Service   │     │  (vectors)  │     │  (convos,   │
└─────────────┘     └─────────────┘     │   config)   │
                                        └─────────────┘
```

### Target State
```
┌─────────────┐     ┌─────────────────────────────────┐
│   Chatbot   │────▶│         PostgreSQL              │
│   Service   │     │  (vectors + convos + config)    │
└─────────────┘     └─────────────────────────────────┘
```

## Implementation Details

### VectorStoreManager Changes

The manager currently supports both ChromaDB and PostgreSQL. We'll simplify to PostgreSQL-only:

```python
# Before (manager.py)
class VectorStoreManager:
    def __init__(self, config):
        if config.get('use_postgres', False):
            self._store = PostgresVectorStore(...)
        else:
            self._store = Chroma(...)  # ChromaDB

# After
class VectorStoreManager:
    def __init__(self, pg_config, embedding_function, collection_name="default"):
        self._store = PostgresVectorStore(
            pg_config=pg_config,
            embedding_function=embedding_function,
            collection_name=collection_name,
        )
```

### Config Schema Change

```yaml
# Before
global:
  chromadb:
    use_HTTP_chromadb_client: true
    host: chromadb
    port: 8000

# After
global:
  vectorstore:
    type: postgres  # Only option now
    collection_name: default
    distance_metric: cosine
```

### Docker Compose Change

```yaml
# Before - 3 services
services:
  chatbot:
    depends_on:
      - chromadb
      - postgres
  chromadb:
    image: chromadb-*
  postgres:
    image: postgres:16

# After - 2 services
services:
  chatbot:
    depends_on:
      - postgres
  postgres:
    image: postgres:16  # with pgvector extension
```

### PostgreSQL Schema Requirements

The `init-v2.sql` already includes:

```sql
-- pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Document chunks with embeddings
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(384),  -- Dimension from embedding model
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- HNSW index for fast similarity search
CREATE INDEX IF NOT EXISTS idx_chunks_embedding 
ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- Full-text search index for BM25
CREATE INDEX IF NOT EXISTS idx_chunks_content_fts 
ON document_chunks USING gin(to_tsvector('english', content));
```

### Migration Path

For existing deployments:

```bash
# 1. Run migration
a2rchi migrate chromadb-to-postgres --deployment cms_simple

# 2. Verify
a2rchi migrate verify --deployment cms_simple

# 3. Update config (automatic with CLI)
a2rchi config update --deployment cms_simple

# 4. Restart without chromadb
a2rchi restart --deployment cms_simple
```

## Compatibility Notes

- Existing embeddings are preserved (same dimensions)
- Query interface unchanged (LangChain VectorStore compatibility)
- Retriever classes work with PostgresVectorStore (already tested)
