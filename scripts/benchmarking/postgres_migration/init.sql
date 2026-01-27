-- PostgreSQL + pgvector benchmark schema
-- Mirrors the proposed production schema for realistic testing

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Document chunks table with vector embeddings and full-text search
CREATE TABLE document_chunks (
    chunk_id SERIAL PRIMARY KEY,
    doc_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI ada-002 dimensions
    metadata JSONB DEFAULT '{}',
    -- Full-text search column (auto-generated)
    chunk_tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', chunk_text)) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity index (HNSW - default for production)
CREATE INDEX idx_chunks_embedding_hnsw ON document_chunks 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Full-text search index
CREATE INDEX idx_chunks_fulltext ON document_chunks USING GIN (chunk_tsv);

-- Trigram index for fuzzy matching (optional)
CREATE INDEX idx_chunks_text_trgm ON document_chunks USING GIN (chunk_text gin_trgm_ops);

-- Compound index for filtering + vector search
CREATE INDEX idx_chunks_doc_id ON document_chunks (doc_id);

-- Analyze table after bulk inserts for query planner
-- (Will be called after data load)
