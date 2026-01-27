# Proposal: Consolidate to PostgreSQL with Static/Dynamic Config Separation

## Summary

Consolidate all database storage to PostgreSQL + pgvector, with document content remaining on the filesystem. Introduce a clear separation between **static configuration** (set at deploy time) and **dynamic configuration** (modifiable at runtime via UI).

> **⚠️ Requires PostgreSQL 17+** - The pg_textsearch extension (used for BM25 full-text search) requires PostgreSQL 17 or later. GA release expected Feb 2026.

> **✅ Partial Implementation (PR #404):** The `CatalogService` has been migrated from SQLite to PostgreSQL. The `resources` table now stores document metadata, and psycopg2 is used for all catalog operations. Legacy SQLite data is not migrated (deprecated). This eliminates one of the three database systems.

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
│  │   (73K dups)│   │             │   │   state         │   │
│  │ • Timing    │   │             │   │                 │   │
│  │ • Tool calls│   │             │   │                 │   │
│  └─────────────┘   └─────────────┘   └─────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Filesystem (/root/data/)                │   │
│  │  • local_files/  • websites/  • tickets/  • git/    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Config File (config.yaml)               │   │
│  │  • Everything in one monolithic YAML                 │   │
│  │  • No runtime modification                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Problems:**
1. Three separate database systems (PostgreSQL, ChromaDB, SQLite)
2. Config table has 73K+ duplicate rows (bug)
3. No separation between deploy-time and runtime configs
4. Can't change models, prompts, or settings without container restart
5. ChromaDB adds container complexity and memory overhead

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      A2rchi Backend                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              PostgreSQL + pgvector                   │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ USERS & AUTH                                         │   │
│  │  • users (identity, auth provider)                   │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ CONVERSATIONS & FEEDBACK                             │   │
│  │  • conversation_metadata, conversations, feedback    │   │
│  │  • timing, agent_tool_calls (traces)                 │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ DOCUMENTS & VECTORS                                  │   │
│  │  • documents (catalog metadata)                      │   │
│  │  • document_chunks (text + embeddings)               │   │
│  │  • user_document_defaults, conversation_doc_overrides│   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ CONFIGURATION                                        │   │
│  │  • static_config (one row, set at deploy)            │   │
│  │  • dynamic_config (runtime settings)                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Filesystem (/root/data/)                │   │
│  │  • local_files/  • websites/  • tickets/  • git/    │   │
│  │  (Document content - not in database)                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Configuration Model

### Static Configuration (Deploy-Time)
Set once when the deployment is created. Requires redeployment to change.

| Setting | Example | Why Static |
|---------|---------|------------|
| `deployment_name` | `cms_simple` | Identity of deployment |
| `data_path` | `/root/data/` | Filesystem structure |
| `postgres.*` | host, port, user | Infrastructure |
| `embedding_model` | `all-MiniLM-L6-v2` | Affects vector dimensions |
| `chunk_size`, `chunk_overlap` | 1000, 150 | Affects existing embeddings |
| `available_pipelines` | `[CMSCompOpsAgent, QAPipeline]` | What's installed |
| `available_models` | `[OpenRouterLLM, OpenAILLM]` | What's available |
| `auth_config` | SSO settings, basic auth | Security infrastructure |
| `byok_encryption_key` | (from env var) | For encrypting API keys |

### Dynamic Configuration (Runtime)
Modifiable via UI without restart.

| Setting | Scope | Example |
|---------|-------|---------|
| `active_pipeline` | global | `CMSCompOpsAgent` |
| `active_model` | global | `openai/gpt-4o` |
| `temperature` | global | `0.7` |
| `system_prompt` | global | Custom agent prompt |
| `num_documents_to_retrieve` | global | `10` |

### User-Level Settings
Per-user preferences and overrides.

| Setting | Example |
|---------|---------|
| `theme` | `dark` / `light` / `system` |
| `preferred_model` | Override global model |
| `api_keys` | BYOK keys (encrypted) |
| `document_defaults` | Which docs enabled by default |

---

## PostgreSQL Schema

### Extensions

```sql
CREATE EXTENSION IF NOT EXISTS vector;       -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS pg_textsearch; -- BM25 full-text search (timescale)
CREATE EXTENSION IF NOT EXISTS pg_trgm;       -- For fuzzy name matching
CREATE EXTENSION IF NOT EXISTS pgcrypto;      -- For API key encryption
```

---

### 1. Users

```sql
-- Central user identity table
-- All user-related tables reference this
CREATE TABLE users (
    id VARCHAR(200) PRIMARY KEY,  -- From auth provider or generated client_id
    
    -- Identity
    display_name TEXT,
    email TEXT,
    auth_provider VARCHAR(50) NOT NULL DEFAULT 'anonymous',  -- 'anonymous', 'basic', 'sso'
    
    -- Preferences (explicit columns for known fields)
    theme VARCHAR(20) NOT NULL DEFAULT 'system',
    preferred_model VARCHAR(200),          -- Override global default
    preferred_temperature NUMERIC(3,2),    -- Override global default
    
    -- BYOK API keys (encrypted with pgcrypto)
    -- Keys stored as: pgp_sym_encrypt(key, encryption_key)
    -- Encryption key comes from BYOK_ENCRYPTION_KEY env var
    api_key_openrouter TEXT,      -- Encrypted
    api_key_openai TEXT,          -- Encrypted  
    api_key_anthropic TEXT,       -- Encrypted
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- For looking up by email (SSO scenarios)
CREATE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL;
```

**API Key Security:**
- Encrypted at rest using `pgp_sym_encrypt()` from pgcrypto
- Encryption key stored in `BYOK_ENCRYPTION_KEY` environment variable
- Application decrypts on read: `pgp_sym_decrypt(api_key_openrouter, $key)`
- Key never logged or exposed in queries

---

### 2. Static Configuration

```sql
-- Single row table for deployment-time configuration
-- Loaded from config.yaml at startup, immutable at runtime
CREATE TABLE static_config (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),  -- Enforce single row
    
    -- Deployment identity
    deployment_name VARCHAR(100) NOT NULL,
    config_version VARCHAR(20) NOT NULL,
    
    -- Paths
    data_path TEXT NOT NULL DEFAULT '/root/data/',
    
    -- Embedding configuration (affects vector dimensions - can't change at runtime)
    embedding_model VARCHAR(200) NOT NULL,
    embedding_dimensions INTEGER NOT NULL,
    chunk_size INTEGER NOT NULL DEFAULT 1000,
    chunk_overlap INTEGER NOT NULL DEFAULT 150,
    distance_metric VARCHAR(20) NOT NULL DEFAULT 'cosine',
    
    -- Available options (what's installed/configured)
    -- Using explicit columns avoids JSONB schema migration issues
    available_pipelines TEXT[] NOT NULL DEFAULT '{}',
    available_models TEXT[] NOT NULL DEFAULT '{}',
    available_providers TEXT[] NOT NULL DEFAULT '{}',
    
    -- Auth configuration
    auth_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

### 3. Dynamic Configuration

```sql
-- Global runtime settings (modifiable via UI)
-- Single row like static_config for simplicity
CREATE TABLE dynamic_config (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),  -- Enforce single row
    
    -- Model settings
    active_pipeline VARCHAR(100) NOT NULL DEFAULT 'CMSCompOpsAgent',
    active_model VARCHAR(200) NOT NULL DEFAULT 'openai/gpt-4o',
    temperature NUMERIC(3,2) NOT NULL DEFAULT 0.7,
    max_tokens INTEGER NOT NULL DEFAULT 4096,
    system_prompt TEXT,  -- NULL = use pipeline default
    
    -- Retrieval settings
    num_documents_to_retrieve INTEGER NOT NULL DEFAULT 10,
    use_hybrid_search BOOLEAN NOT NULL DEFAULT TRUE,
    bm25_weight NUMERIC(3,2) NOT NULL DEFAULT 0.3,
    semantic_weight NUMERIC(3,2) NOT NULL DEFAULT 0.7,
    
    -- Metadata
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(200)  -- user_id who made the change
);

-- Initialize with defaults
INSERT INTO dynamic_config (id) VALUES (1) ON CONFLICT DO NOTHING;
```

---

### 4. Documents & Vectors

```sql
-- Document catalog (replaces SQLite catalog.sqlite)
-- Content stays on filesystem, only metadata in DB
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    resource_hash VARCHAR(64) UNIQUE NOT NULL,
    
    -- File location (relative to data_path)
    file_path TEXT NOT NULL,
    
    -- Display info
    display_name TEXT NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- 'local_files', 'web', 'ticket', 'git'
    
    -- Source-specific fields
    url TEXT,                    -- For web sources
    ticket_id VARCHAR(100),      -- For ticket sources
    git_repo VARCHAR(200),       -- For git sources
    git_commit VARCHAR(64),      -- For git sources
    
    -- File metadata
    suffix VARCHAR(20),
    size_bytes BIGINT,
    mime_type VARCHAR(100),
    
    -- Provenance
    original_path TEXT,
    base_path TEXT,              -- For relative path reconstruction
    relative_path TEXT,          -- Path relative to base_path
    
    -- Extensible metadata (for source-specific fields not in columns)
    extra_json JSONB,            -- Structured extra metadata
    extra_text TEXT,             -- Searchable text representation
    
    -- Timestamps
    file_modified_at TIMESTAMP,
    ingested_at TIMESTAMP,
    indexed_at TIMESTAMP,        -- When embeddings were created
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Soft delete
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    
    CONSTRAINT valid_source CHECK (source_type IN ('local_files', 'web', 'ticket', 'git'))
);

CREATE INDEX idx_documents_hash ON documents(resource_hash);
CREATE INDEX idx_documents_source ON documents(source_type);
CREATE INDEX idx_documents_name ON documents USING gin (display_name gin_trgm_ops);
CREATE INDEX idx_documents_active ON documents(is_deleted) WHERE NOT is_deleted;

-- Document chunks with embeddings (replaces ChromaDB)
-- Note: Vector dimension (384) must match static_config.embedding_dimensions
-- Changing embedding models requires re-creating this table
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    
    -- Chunk content
    chunk_text TEXT NOT NULL,
    
    -- Vector embedding (dimension set at deploy time)
    -- 384 = all-MiniLM-L6-v2, 1536 = text-embedding-ada-002
    embedding vector(384),
    
    -- Note: BM25 full-text search uses pg_textsearch index on chunk_text directly
    -- No tsvector column needed - pg_textsearch creates its own index structure
    
    -- Chunk metadata
    start_char INTEGER,
    end_char INTEGER,
    metadata JSONB,              -- Original document metadata propagated to chunk
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX idx_chunks_document ON document_chunks(document_id);

-- Vector index (type configurable: hnsw, ivfflat, or none)
-- Default: HNSW - doesn't require training data, good balance of speed/accuracy
CREATE INDEX idx_chunks_embedding ON document_chunks 
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- BM25 full-text search index (pg_textsearch)
-- Provides proper BM25 ranking with configurable k1/b parameters
CREATE INDEX idx_chunks_bm25 ON document_chunks 
    USING bm25(chunk_text) WITH (text_config='english');
```

---

### 5. Document Selections (3-Tier System)

```sql
-- System default: all documents enabled (no table needed - implicit)

-- User defaults: power users can disable docs globally for themselves
-- Only stores opt-outs (if row exists and enabled=FALSE, doc is disabled)
CREATE TABLE user_document_defaults (
    user_id VARCHAR(200) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,  -- FALSE = opted out
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (user_id, document_id)
);

CREATE INDEX idx_user_doc_defaults_user ON user_document_defaults(user_id);

-- Conversation overrides: override user default for a specific conversation
-- Only stores differences from user default
CREATE TABLE conversation_document_overrides (
    conversation_id INTEGER NOT NULL REFERENCES conversation_metadata(conversation_id) ON DELETE CASCADE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL,  -- Explicit override value
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (conversation_id, document_id)
);

CREATE INDEX idx_conv_doc_overrides_conv ON conversation_document_overrides(conversation_id);
```

**Selection Logic:**
```sql
-- Get effective enabled state for a document in a conversation
-- Priority: conversation_override > user_default > system_default (true)
SELECT 
    d.id,
    d.display_name,
    COALESCE(
        cdo.enabled,                    -- 1. Conversation override
        udd.enabled,                    -- 2. User default  
        TRUE                            -- 3. System default (all enabled)
    ) AS enabled
FROM documents d
LEFT JOIN user_document_defaults udd 
    ON udd.document_id = d.id AND udd.user_id = $user_id
LEFT JOIN conversation_document_overrides cdo 
    ON cdo.document_id = d.id AND cdo.conversation_id = $conversation_id
WHERE NOT d.is_deleted;
```

---

### 6. Conversations & Chat

```sql
-- Conversation metadata
CREATE TABLE conversation_metadata (
    conversation_id SERIAL PRIMARY KEY,
    user_id VARCHAR(200) REFERENCES users(id) ON DELETE SET NULL,
    title TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMP NOT NULL DEFAULT NOW(),
    a2rchi_version VARCHAR(50)
);

CREATE INDEX idx_conv_meta_user ON conversation_metadata(user_id);

-- Individual messages
CREATE TABLE conversations (
    message_id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversation_metadata(conversation_id) ON DELETE CASCADE,
    
    a2rchi_service TEXT NOT NULL,
    sender TEXT NOT NULL,
    content TEXT NOT NULL,
    
    -- Capture what was actually used (for Grafana analytics)
    -- These replace the old conf_id foreign key to configs table
    model_used VARCHAR(200),
    pipeline_used VARCHAR(100),
    
    -- RAG context
    link TEXT NOT NULL DEFAULT '',
    context TEXT NOT NULL DEFAULT '',
    
    ts TIMESTAMP NOT NULL
);

CREATE INDEX idx_conversations_conv ON conversations(conversation_id);
CREATE INDEX idx_conversations_ts ON conversations(ts);

-- Feedback on messages (supports multiple feedback entries per message)
CREATE TABLE feedback (
    mid INTEGER NOT NULL REFERENCES conversations(message_id) ON DELETE CASCADE,
    feedback_ts TIMESTAMP NOT NULL,
    feedback TEXT NOT NULL,           -- 'like', 'dislike', 'comment'
    feedback_msg TEXT,                -- Optional text feedback/comment
    incorrect BOOLEAN,                -- Flag: response was factually incorrect
    unhelpful BOOLEAN,                -- Flag: response didn't help
    inappropriate BOOLEAN,            -- Flag: response was inappropriate
    
    PRIMARY KEY (mid, feedback_ts)    -- Allows multiple feedback entries per message
);

CREATE INDEX idx_feedback_mid ON feedback(mid);

-- Response timing metrics (detailed breakdown for performance analysis)
CREATE TABLE timing (
    mid INTEGER PRIMARY KEY REFERENCES conversations(message_id) ON DELETE CASCADE,
    client_sent_msg_ts TIMESTAMP NOT NULL,
    server_received_msg_ts TIMESTAMP NOT NULL,
    lock_acquisition_ts TIMESTAMP NOT NULL,
    vectorstore_update_ts TIMESTAMP NOT NULL,
    query_convo_history_ts TIMESTAMP NOT NULL,
    chain_finished_ts TIMESTAMP NOT NULL,
    a2rchi_message_ts TIMESTAMP NOT NULL,
    insert_convo_ts TIMESTAMP NOT NULL,
    finish_call_ts TIMESTAMP NOT NULL,
    server_response_msg_ts TIMESTAMP NOT NULL,
    msg_duration INTERVAL NOT NULL     -- Total duration (server_response - server_received)
);
```

---

### 7. Agent Traces

```sql
-- Agent tool call traces (existing table, documented here for completeness)
-- Stores each step of agent execution for debugging and analytics
CREATE TABLE agent_tool_calls (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversation_metadata(conversation_id) ON DELETE CASCADE,
    message_id INTEGER NOT NULL REFERENCES conversations(message_id) ON DELETE CASCADE,
    
    -- Step within the agent's execution
    step_number INTEGER NOT NULL,
    
    -- Tool invocation details
    tool_name VARCHAR(100) NOT NULL,
    tool_args JSONB,           -- Arguments passed to tool
    tool_result TEXT,          -- Result returned by tool
    
    ts TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tool_calls_message ON agent_tool_calls(message_id);
CREATE INDEX idx_tool_calls_conv ON agent_tool_calls(conversation_id);
CREATE INDEX idx_tool_calls_tool ON agent_tool_calls(tool_name);
```

---

### 8. A/B Comparison Tracking (Existing Feature)

```sql
-- A/B comparison tracking for preference collection
-- Note: Previously referenced configs table; now tracks model/pipeline directly
CREATE TABLE ab_comparisons (
    comparison_id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversation_metadata(conversation_id) ON DELETE CASCADE,
    user_prompt_mid INTEGER NOT NULL REFERENCES conversations(message_id) ON DELETE CASCADE,
    response_a_mid INTEGER NOT NULL REFERENCES conversations(message_id) ON DELETE CASCADE,
    response_b_mid INTEGER NOT NULL REFERENCES conversations(message_id) ON DELETE CASCADE,
    
    -- Model/pipeline info (replaces config_a_id, config_b_id foreign keys)
    -- The actual config is now captured in conversations.model_used/pipeline_used
    model_a VARCHAR(200) NOT NULL,
    model_b VARCHAR(200) NOT NULL,
    pipeline_a VARCHAR(100),
    pipeline_b VARCHAR(100),
    
    is_config_a_first BOOLEAN NOT NULL,  -- For randomization tracking
    preference VARCHAR(10),               -- 'a', 'b', 'tie', or NULL (not yet voted)
    preference_ts TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ab_comparisons_conversation ON ab_comparisons(conversation_id);
CREATE INDEX idx_ab_comparisons_models ON ab_comparisons(model_a, model_b);
CREATE INDEX idx_ab_comparisons_preference ON ab_comparisons(preference) WHERE preference IS NOT NULL;
CREATE INDEX idx_ab_comparisons_pending ON ab_comparisons(conversation_id) WHERE preference IS NULL;
```

---

### 10. Grafana Access

```sql
-- Read-only user for Grafana dashboards
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'grafana') THEN
        CREATE USER grafana WITH PASSWORD 'GRAFANA_PG_PASSWORD';
    END IF;
END $$;

GRANT USAGE ON SCHEMA public TO grafana;
GRANT SELECT ON 
    users,
    static_config,
    dynamic_config,
    documents,
    document_chunks,
    conversation_metadata,
    conversations,
    feedback,
    timing,
    agent_tool_calls,
    ab_comparisons
TO grafana;

-- Note: Grafana queries that used configs.config_name should now use:
-- - static_config.deployment_name for deployment identity
-- - conversations.model_used for per-message model tracking
-- - ab_comparisons.model_a/model_b for A/B test analysis
```

---

## Service Compatibility Analysis

### Services Impact Assessment

| Service | CatalogService | ChromaDB | PostgreSQL | Impact |
|---------|---------------|----------|------------|--------|
| **chat_app** | ✅ Already PG | ⚠️ Via A2rchi | ✅ Direct | VectorstoreConnector change |
| **redmine** | ✅ Already PG | ⚠️ Via A2rchi | ✅ Direct | VectorstoreConnector change |
| **mailbox** | ✅ Via redmine | ⚠️ Via redmine | ✅ Via redmine | No direct changes needed |
| **data_manager** | ✅ Already PG | ⚠️ VectorStoreManager | ✅ Direct | VectorStoreManager change |
| **uploader_app** | ✅ Already PG | ❌ None | ✅ Direct | No changes needed |
| **grader_app** | ✅ Already PG | ⚠️ Via A2rchi | ✅ Direct | VectorstoreConnector change |

### Key Integration Points

**1. VectorstoreConnector** (`src/a2rchi/utils/vectorstore_connector.py`)
- Currently returns `langchain_chroma.Chroma` instance
- Must be updated to return `PostgresVectorStore`
- **All callers unchanged** - they expect `VectorStore` interface

**2. VectorStoreManager** (`src/data_manager/vectorstore/manager.py`)
- Currently uses `chromadb` directly for ingestion
- Must be updated to use PostgreSQL
- **All callers unchanged** - DataManager API stays same

**3. CatalogService** (`src/data_manager/collectors/utils/index_utils.py`)
- ✅ **Already migrated to PostgreSQL** (PR #404)
- No changes needed

### Backward Compatibility Guarantees

1. **LangChain VectorStore interface preserved** - PostgresVectorStore implements same interface as Chroma
2. **Config path migration** - `services.chromadb` → `services.postgres.vectorstore` with deprecation warning
3. **No API changes** - All Flask endpoints remain identical
4. **Redmine/Mailer services** - No code changes required, just config
5. **DataManager API** - `update_vectorstore()` signature unchanged

---

## Migration Plan

### Phase 1: Schema Setup
1. Create new tables with pgvector extension
2. Insert static_config from config.yaml (one-time on deploy)
3. Insert dynamic_config defaults
4. Migrate documents from catalog.sqlite
5. Re-embed documents to document_chunks (or migrate from ChromaDB if possible)

### Phase 2: Code Updates
1. Add `users` table population (create on first interaction)
2. Replace `CatalogService` SQLite → PostgreSQL
3. Replace ChromaDB client → `PostgresVectorStore`
4. Add `ConfigService` with static/dynamic separation
5. Update chat app to write `model_used` to conversations
6. Add UI endpoints for dynamic config editing

### Phase 3: Cleanup
1. Remove ChromaDB from docker-compose
2. Remove SQLite files from data volume
3. Drop old `configs` table (with 73K duplicates)
4. Update Grafana dashboard queries
5. Update deployment scripts

---

## Configuration & Deployment

### Docker Setup

We'll create a custom PostgreSQL 17 image with pgvector and pg_textsearch:

```dockerfile
# Dockerfile-postgres
# Note: pg_textsearch requires PostgreSQL 17+ 
FROM postgres:17

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-17 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pgvector
RUN cd /tmp \
    && git clone --branch v0.7.4 https://github.com/pgvector/pgvector.git \
    && cd pgvector \
    && make \
    && make install \
    && rm -rf /tmp/pgvector

# Install pg_textsearch (BM25)
# Download pre-built binary from releases
RUN cd /tmp \
    && curl -LO https://github.com/timescale/pg_textsearch/releases/download/v0.4.2/pg_textsearch-0.4.2-pg17-linux-arm64.tar.gz \
    && tar xzf pg_textsearch-*.tar.gz \
    && cp pg_textsearch-*/lib/* $(pg_config --pkglibdir)/ \
    && cp pg_textsearch-*/share/extension/* $(pg_config --sharedir)/extension/ \
    && rm -rf /tmp/pg_textsearch*

# Cleanup
RUN apt-get remove -y build-essential git postgresql-server-dev-17 \
    && apt-get autoremove -y
```

Alternative: Use pre-built `pgvector/pgvector:pg16` image.

### Static Configuration (config.yaml)

These settings are read at deploy time and stored in `static_config` table:

```yaml
# config.yaml - Static settings (require redeployment to change)

deployment:
  name: "cms_simple"
  version: "2.0.0"
  data_path: "/root/data/"

# Database settings
services:
  postgres:
    host: "postgres"
    port: 5432
    user: "a2rchi"
    database: "a2rchi-db"
    # Password from environment: POSTGRES_PASSWORD

# Embedding configuration (CANNOT change without re-indexing all documents)
embedding:
  model: "all-MiniLM-L6-v2"
  dimensions: 384
  # Model class mapping
  class_map:
    all-MiniLM-L6-v2:
      class: "HuggingFaceEmbeddings"
      kwargs:
        model_name: "sentence-transformers/all-MiniLM-L6-v2"
    text-embedding-3-small:
      class: "OpenAIEmbeddings"
      kwargs:
        model: "text-embedding-3-small"

# Chunking configuration (CANNOT change without re-indexing)
chunking:
  size: 1000
  overlap: 150

# Vector index configuration
vector_index:
  # Options: "hnsw", "ivfflat", "none"
  # - hnsw: Fast, no training required, good for most cases
  # - ivfflat: Faster for very large datasets, requires training after data load
  # - none: Exact search, slow but accurate (for small datasets or testing)
  type: "hnsw"
  
  # HNSW parameters (only used if type=hnsw)
  hnsw:
    m: 16                    # Max connections per node (higher = more accurate, more memory)
    ef_construction: 64      # Build-time search width (higher = better quality, slower build)
  
  # IVFFlat parameters (only used if type=ivfflat)
  ivfflat:
    lists: 100               # Number of clusters (sqrt(n) is good starting point)

# Full-text search configuration (pg_textsearch / BM25)
text_search:
  # pg_textsearch provides true BM25 ranking (https://github.com/timescale/pg_textsearch)
  language: "english"        # PostgreSQL text search config for stemming/stop words
  # BM25 parameters
  k1: 1.2                    # Term frequency saturation (default 1.2)
  b: 0.75                    # Length normalization (default 0.75)
  # Weights for hybrid search (semantic + BM25)
  weights:
    semantic: 0.7            # Vector similarity weight
    bm25: 0.3                # BM25 text search weight

# Available options (what's installed - restricts dynamic config choices)
available:
  pipelines:
    - "CMSCompOpsAgent"
    - "QAPipeline"
    - "SimpleChatPipeline"
  models:
    - "openai/gpt-4o"
    - "openai/gpt-4o-mini"
    - "anthropic/claude-3.5-sonnet"
    - "meta-llama/llama-3.1-70b-instruct"
  providers:
    - "openrouter"
    - "openai"
    - "anthropic"

# Authentication (infrastructure - requires redeployment)
auth:
  enabled: false
  # SSO configuration would go here
```

### Dynamic Configuration (Database)

These are stored in `dynamic_config` table and editable via UI:

```yaml
# Initial values inserted into dynamic_config table
# Users can change these at runtime without restart

# Model settings
active_pipeline: "CMSCompOpsAgent"
active_model: "openai/gpt-4o"
temperature: 0.7
max_tokens: 4096
system_prompt: null  # null = use pipeline default

# Retrieval settings
num_documents_to_retrieve: 10
use_hybrid_search: true
```

### Environment Variables

```bash
# Required secrets (not in config.yaml)
POSTGRES_PASSWORD=<secure-password>
GRAFANA_PG_PASSWORD=<grafana-readonly-password>
BYOK_ENCRYPTION_KEY=<32-byte-base64-key>  # For encrypting user API keys

# Optional provider API keys (if not using BYOK)
OPENROUTER_API_KEY=<key>
OPENAI_API_KEY=<key>
```

### Docker Compose Changes

```yaml
services:
  postgres:
    # Change from postgres:16 to custom image with pgvector
    image: a2rchi-postgres:${VERSION}
    build:
      context: .
      dockerfile: Dockerfile-postgres
    container_name: postgres-${DEPLOYMENT_NAME}
    environment:
      POSTGRES_USER: a2rchi
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: a2rchi-db
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U a2rchi -d a2rchi-db"]
      interval: 5s
      timeout: 5s
      retries: 5

  # REMOVED: chromadb service
  # chromadb:
  #   image: chromadb/chroma:latest
  #   ...

  chat:
    depends_on:
      postgres:
        condition: service_healthy
      # REMOVED: chromadb dependency
    environment:
      # Add encryption key for BYOK
      BYOK_ENCRYPTION_KEY: ${BYOK_ENCRYPTION_KEY}
```

### Deployment Process

#### New Deployment
```bash
# 1. Generate config from template
a2rchi init my-deployment

# 2. Edit config.yaml with your settings
vim ~/.a2rchi/my-deployment/config.yaml

# 3. Set secrets
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export BYOK_ENCRYPTION_KEY=$(openssl rand -base64 32)

# 4. Deploy
a2rchi up my-deployment

# 5. Verify
a2rchi status my-deployment
```

#### Migration from Existing Deployment (ChromaDB → PostgreSQL)

```bash
# 1. Backup existing data
a2rchi backup my-deployment --output backup-$(date +%Y%m%d).tar.gz

# 2. Stop services (brief downtime starts here)
a2rchi stop my-deployment

# 3. Update to new version with PostgreSQL-only
a2rchi upgrade my-deployment --version 2.0.0

# 4. Run migration script
a2rchi migrate my-deployment --from-chromadb

# This does:
# - Creates new PostgreSQL tables
# - Migrates catalog.sqlite → documents table
# - Re-embeds all documents to document_chunks (or imports from ChromaDB)
# - Migrates chat_document_selections → user_document_defaults
# - Drops old configs table
# - Removes ChromaDB data

# 5. Start services (downtime ends)
a2rchi up my-deployment

# 6. Verify
a2rchi status my-deployment
```

**Migration Downtime**: The downtime is the period between `stop` and `up`. For a typical deployment:
- Small (< 100 docs): ~2-5 minutes
- Medium (100-1000 docs): ~10-30 minutes (mostly re-embedding)
- Large (1000+ docs): ~1-2 hours

The re-embedding step is the bottleneck. Options to reduce downtime:
1. Pre-migrate in parallel (dual-write) - complex
2. Accept downtime window
3. Migrate embeddings from ChromaDB without re-computing (if formats compatible)

### init.sql Updates

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;       -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS pg_textsearch; -- BM25 full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- For fuzzy name matching  
CREATE EXTENSION IF NOT EXISTS pgcrypto;     -- For API key encryption

-- Create tables (as defined in schema section above)
-- ...

-- Create vector index based on config
-- This is templated based on vector_index.type setting:

{% if vector_index_type == 'hnsw' %}
CREATE INDEX idx_chunks_embedding ON document_chunks 
    USING hnsw (embedding vector_cosine_ops) 
    WITH (m = {{ vector_index_hnsw_m }}, ef_construction = {{ vector_index_hnsw_ef }});
{% elif vector_index_type == 'ivfflat' %}
-- Note: IVFFlat index should be created AFTER data is loaded
-- This is just a placeholder; actual index created by migration script
CREATE INDEX idx_chunks_embedding ON document_chunks 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = {{ vector_index_ivfflat_lists }});
{% else %}
-- No index (exact search)
{% endif %}

-- BM25 full-text search index (pg_textsearch)
-- Creates native BM25 index with configurable parameters
CREATE INDEX idx_chunks_bm25 ON document_chunks 
    USING bm25(chunk_text) 
    WITH (text_config='{{ text_search_language }}', k1={{ text_search_k1 }}, b={{ text_search_b }});
```

### Hybrid Search Implementation

```sql
-- Hybrid search combining semantic (pgvector) + BM25 (pg_textsearch)
-- Called from PostgresVectorStore.similarity_search()

WITH semantic_results AS (
    -- Get top candidates via vector similarity
    SELECT 
        dc.id,
        dc.document_id,
        dc.chunk_text,
        dc.metadata,
        1 - (dc.embedding <=> $1::vector) AS semantic_score  -- cosine similarity [0,1]
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE NOT d.is_deleted
    ORDER BY dc.embedding <=> $1::vector
    LIMIT $2 * 2  -- Fetch extra for re-ranking
),
bm25_results AS (
    -- Get BM25 scores for the query
    -- pg_textsearch uses <@> operator which returns negative scores (lower = better match)
    -- We negate to get positive scores where higher = better
    SELECT 
        dc.id,
        -(dc.chunk_text <@> to_bm25query($3, 'idx_chunks_bm25')) AS bm25_score
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE NOT d.is_deleted
      AND dc.chunk_text <@> to_bm25query($3, 'idx_chunks_bm25') < 0  -- Has a match
),
combined AS (
    SELECT 
        sr.id,
        sr.document_id,
        sr.chunk_text,
        sr.metadata,
        sr.semantic_score,
        COALESCE(br.bm25_score, 0) AS bm25_score,
        -- Normalize and combine scores
        -- semantic_score is already [0,1], bm25 needs normalization
        (sr.semantic_score * $4) + 
        (COALESCE(br.bm25_score, 0) / NULLIF(MAX(br.bm25_score) OVER (), 0) * $5) AS combined_score
    FROM semantic_results sr
    LEFT JOIN bm25_results br ON sr.id = br.id
)
SELECT id, document_id, chunk_text, metadata, combined_score
FROM combined
ORDER BY combined_score DESC
LIMIT $2;

-- Parameters:
-- $1: query embedding vector
-- $2: k (number of results)  
-- $3: query text for BM25 search
-- $4: semantic weight (e.g., 0.7)
-- $5: bm25 weight (e.g., 0.3)
```

---

## API Endpoints

```
# Static config (read-only)
GET  /api/config/static

# Dynamic config (admin only)
GET  /api/config/dynamic
PUT  /api/config/dynamic

# User profile & preferences
GET  /api/user/profile
PUT  /api/user/profile
POST /api/user/api-keys/:provider    # Add encrypted BYOK key
DELETE /api/user/api-keys/:provider  # Remove key

# Document selections
GET  /api/user/document-defaults
PUT  /api/user/document-defaults/:doc_id
GET  /api/conversations/:id/document-overrides
PUT  /api/conversations/:id/document-overrides/:doc_id
```

---

## Benchmarking Plan

Before full implementation, run synthetic benchmarks:

### 1. Vector Search: pgvector vs ChromaDB
```python
# Benchmark script outline
datasets = [100, 1000, 10000, 100000]  # Number of documents
queries = generate_random_queries(100)

for n in datasets:
    # Setup both stores with same embeddings
    chroma_store = setup_chromadb(n)
    pg_store = setup_pgvector(n)
    
    # Benchmark queries
    chroma_times = [time_query(chroma_store, q) for q in queries]
    pg_times = [time_query(pg_store, q) for q in queries]
    
    print(f"n={n}: ChromaDB p50={p50(chroma_times)}ms, pgvector p50={p50(pg_times)}ms")
```

### 2. Text Search: pg_fulltext vs in-memory BM25
```python
# Compare PostgreSQL full-text search vs LangChain BM25Retriever
for n in datasets:
    docs = load_documents(n)
    
    # Setup both
    bm25 = BM25Retriever.from_documents(docs)  # In-memory
    pg_fts = setup_pg_fulltext(docs)           # PostgreSQL
    
    # Benchmark
    bm25_times = [time_query(bm25, q) for q in queries]
    pg_times = [time_query(pg_fts, q) for q in queries]
    
    print(f"n={n}: BM25 p50={p50(bm25_times)}ms, pg_fts p50={p50(pg_times)}ms")
```

**Success criteria**: pgvector and pg_fulltext should be within 2x of ChromaDB/BM25 latency for datasets up to 10K documents.

---

## Success Criteria

1. ✅ Single PostgreSQL database (ChromaDB removed)
2. ✅ No SQLite files in deployment
3. ✅ Static config loaded once at startup, immutable
4. ✅ Dynamic config editable via UI without restart
5. ✅ BYOK keys encrypted at rest with pgcrypto
6. ✅ Document content remains on filesystem
7. ✅ Vector search via pgvector works correctly
8. ✅ 3-tier document selection (system → user → conversation)
9. ✅ Agent traces queryable in Grafana
10. ✅ All existing UI tests pass

---

## Effort Estimate

| Task | Estimate |
|------|----------|
| Schema design and init.sql | 2 hours |
| Users table + BYOK encryption | 2 hours |
| ConfigService (static/dynamic) | 3 hours |
| PostgresVectorStore implementation | 4 hours |
| CatalogService PostgreSQL migration | 2 hours |
| 3-tier document selection logic | 2 hours |
| Config/User API endpoints | 3 hours |
| Migration script | 3 hours |
| Docker compose updates | 1 hour |
| Grafana dashboard updates | 2 hours |
| Testing and debugging | 4 hours |
| Documentation | 1 hour |
| **Total** | **~29 hours** |

---

## Review: Risks, Gaps, and Uncertainties

### 🔴 CRITICAL ISSUES ~~(Must Fix Before Implementation)~~ → ALL FIXED

#### 1. ~~Missing Feedback Table Columns~~ ✅ FIXED
**Current schema** has `feedback_msg`, `incorrect`, `unhelpful`, `inappropriate` columns that are actively used.
~~**Proposed schema** only has `feedback` (like/dislike) and `feedback_ts`.~~

**Status**: ✅ FIXED - All feedback columns now included with composite PK `(mid, feedback_ts)`.

#### 2. ~~Missing Timing Table Columns~~ ✅ FIXED
**Current schema** has detailed timing breakdown (10+ columns). ~~**Proposed schema** only has 3 columns.~~

**Status**: ✅ FIXED - All 11 timing columns now included in proposal.

#### 3. ~~Missing `ab_comparisons` Table~~ ✅ FIXED
The proposal completely omits the A/B testing table which has foreign keys to configs.

**Status**: ✅ FIXED - Added ab_comparisons table with model_a/model_b columns replacing config FKs.

---

### 🟡 MEDIUM ISSUES (Address During Implementation)

#### 4. LangChain Integration Uncertainty
Current code uses `langchain_chroma.Chroma` which provides `.similarity_search_with_score()`.
Proposal needs a `PostgresVectorStore` that implements `VectorStore` interface.

```python
# src/a2rchi/utils/vectorstore_connector.py
vectorstore = Chroma(
    client=client,
    collection_name=self.collection_name,
    embedding_function=self.embedding_model,
)
```

**Answer**: `langchain-postgres` package exists and provides `PGVector` class. See [LangChain pgvector docs](https://python.langchain.com/docs/integrations/vectorstores/pgvector/).
**Action**: Use `langchain-postgres` package, verify API compatibility.

#### 5. Chunk Metadata Lost
Current ChromaDB stores rich metadata per chunk:
```python
# manager.py line 227-231
entry_metadata = {**file_level_metadata, **doc_metadata}
entry_metadata["chunk_index"] = index
entry_metadata["filename"] = filename
entry_metadata["resource_hash"] = filehash
```

**Status**: ✅ FIXED - Added `metadata JSONB` column to document_chunks table.

#### 6. Vector Dimension Hardcoded
Proposal hardcodes `vector(384)` but this depends on embedding model:
- `all-MiniLM-L6-v2`: 384 dimensions
- `text-embedding-ada-002`: 1536 dimensions
- Other models vary

**Status**: ✅ DOCUMENTED - Added comment noting dimension must match static_config.embedding_dimensions and changing models requires re-creating table.

#### 7. ~~IVFFlat Index Requires Training~~ ✅ FIXED
~~IVFFlat indexes need data to exist before creation for optimal performance.~~
**Status**: ✅ FIXED - Changed to HNSW index which doesn't require training data.

---

### 🟢 MINOR ISSUES (Nice to Fix) - MOSTLY ADDRESSED

#### 8. ~~`conversations.conf_id` Removal Breaking Change~~ ✅ ADDRESSED
Current table has `conf_id INTEGER NOT NULL REFERENCES configs`. This is used for:
- Grafana queries joining conversations to config_name
- A/B comparison tracking

**Status**: ✅ ADDRESSED - `model_used` and `pipeline_used` columns added to proposal. Code updates needed for SQL_INSERT_CONVO.

#### 9. ~~Feedback Primary Key Mismatch~~ ✅ FIXED
- **Current**: `PRIMARY KEY (mid, feedback_ts)` - allows multiple feedback entries per message
- ~~**Proposed**: `PRIMARY KEY (mid)` - only one feedback per message~~

**Status**: ✅ FIXED - Proposal now uses composite PK `(mid, feedback_ts)` matching current behavior.

#### 10. ~~Missing `extra_json` and `extra_text` Columns~~ ✅ FIXED
Current SQLite catalog has `extra_json` and `extra_text` for extensible metadata.
~~Proposed `documents` table doesn't have these.~~

**Status**: ✅ FIXED - Added `extra_json JSONB` and `extra_text TEXT` columns to documents table.

---

### ❓ OPEN QUESTIONS → ALL RESOLVED

1. **pgvector Docker image**: Does the standard `postgres:16` image include pgvector, or do we need a custom image?
   - ✅ **RESOLVED**: Build custom Dockerfile extending `postgres:16` that installs pgvector. See "Docker Setup" section.

2. **Migration downtime**: Can we do a zero-downtime migration, or will there be a cutover period?
   - ✅ **RESOLVED**: Brief cutover required. Downtime depends on document count:
     - Small (< 100 docs): ~2-5 minutes
     - Medium (100-1000 docs): ~10-30 minutes  
     - Large (1000+ docs): ~1-2 hours (re-embedding is bottleneck)

3. **Hybrid search**: How does BM25/keyword search work with PostgreSQL?
   - ✅ **RESOLVED**: Use pg_textsearch extension for true BM25 ranking. Creates native BM25 index on `chunk_text` column. See "Hybrid Search Implementation" section.

4. **Performance benchmarks**: Should we benchmark before committing?
   - ✅ **RESOLVED**: Yes, run synthetic benchmarks:
     - pgvector vs ChromaDB (vector search)
     - pg_fulltext vs in-memory BM25 (keyword search)
   - Success criteria: Within 2x latency for datasets up to 10K documents.

5. **Grafana dashboard compatibility**: Will we maintain backward compatibility?
   - ✅ **RESOLVED**: Update existing dashboards to use `conversations.model_used` instead of configs join.

---

### ✅ CONFIRMED CORRECT

1. **Static vs Dynamic config split** - Well designed
2. **3-tier document selections** - Good user model
3. **Users table** - Needed for proper FK relationships
4. **Agent traces** - Already matches existing schema
5. **pgcrypto for API keys** - Standard PostgreSQL approach
6. **Document content on filesystem** - Correct, don't store blobs in DB
7. **Configurable vector index** - HNSW/IVFFlat/none options added
8. **BM25 full-text search** - pg_textsearch with configurable k1/b parameters

---

## References

- [pgvector documentation](https://github.com/pgvector/pgvector)
- [pg_textsearch](https://github.com/timescale/pg_textsearch) - Timescale's BM25 extension for PostgreSQL 17+
- [pgcrypto for encryption](https://www.postgresql.org/docs/current/pgcrypto.html)
- [langchain-postgres](https://python.langchain.com/docs/integrations/vectorstores/pgvector/) - LangChain pgvector integration
