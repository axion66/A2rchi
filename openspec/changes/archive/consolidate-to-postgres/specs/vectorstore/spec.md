## ADDED Requirements

### Requirement: PostgresVectorStore
The system SHALL provide a `PostgresVectorStore` class implementing vector storage and retrieval using pgvector, replacing ChromaDB.

#### Scenario: LangChain VectorStore interface
- **WHEN** PostgresVectorStore is instantiated
- **THEN** it implements `langchain_core.vectorstores.base.VectorStore`
- **AND** `similarity_search(query, k)` returns `List[Document]`
- **AND** `similarity_search_with_score(query, k)` returns `List[Tuple[Document, float]]`
- **AND** it is a drop-in replacement for `langchain_chroma.Chroma`

#### Scenario: VectorstoreConnector compatibility
- **WHEN** `VectorstoreConnector.get_vectorstore()` is called
- **THEN** it returns `PostgresVectorStore` instead of `Chroma`
- **AND** all existing callers (A2rchi, redmine, mailer services) work unchanged
- **AND** the return type still satisfies `VectorStore` interface

#### Scenario: VectorStoreManager compatibility  
- **WHEN** `VectorStoreManager.update_vectorstore()` is called
- **THEN** it upserts documents to PostgreSQL instead of ChromaDB
- **AND** `VectorStoreManager.fetch_collection()` returns a PostgresVectorStore
- **AND** all existing callers (DataManager, uploader) work unchanged

#### Scenario: Add documents with embeddings
- **WHEN** `add_documents(documents, embeddings)` is called
- **THEN** document chunks are inserted into `document_chunks` table
- **AND** embeddings are stored as vector type
- **AND** metadata is stored as JSONB

#### Scenario: Query embedding
- **WHEN** `similarity_search(query_text, k)` is called with text input
- **THEN** query_text is embedded using the configured embedding model
- **AND** the resulting vector is used for similarity search

#### Scenario: Similarity search
- **WHEN** `similarity_search(query_embedding, k)` is called
- **THEN** the top k most similar chunks are returned
- **AND** results are ordered by cosine similarity (descending)
- **AND** only non-deleted documents are searched

#### Scenario: Delete document chunks
- **WHEN** a document is soft-deleted in the documents table
- **THEN** its chunks are excluded from search results
- **AND** chunks can be permanently deleted via `delete_document(document_id)`

#### Scenario: HNSW index usage
- **WHEN** similarity search is performed with HNSW index configured
- **THEN** the query uses the HNSW index for approximate nearest neighbor
- **AND** performance is sub-linear with respect to dataset size

---

### Requirement: Hybrid Search
The system SHALL support hybrid search combining semantic similarity (pgvector) with BM25 text ranking (pg_textsearch).

#### Scenario: Hybrid search execution
- **WHEN** `hybrid_search(query_embedding, query_text, k)` is called
- **THEN** semantic scores are computed using pgvector cosine distance
- **AND** BM25 scores are computed using pg_textsearch `<@>` operator
- **AND** scores are combined: `(semantic × weight) + (bm25 × weight)`
- **AND** results are sorted by combined score

#### Scenario: BM25 score normalization
- **WHEN** combining semantic and BM25 scores
- **THEN** BM25 scores are normalized to [0,1] range
- **AND** pg_textsearch negative scores are negated before normalization

#### Scenario: Configurable hybrid weights
- **WHEN** hybrid search is performed
- **THEN** semantic_weight and bm25_weight are read from dynamic_config
- **AND** default weights are 0.7 semantic, 0.3 BM25

#### Scenario: BM25 parameter configuration
- **WHEN** the BM25 index is created
- **THEN** k1 (term saturation) and b (length normalization) are configurable
- **AND** default values are k1=1.2, b=0.75

#### Scenario: BM25 unavailable fallback
- **WHEN** pg_textsearch extension is not available
- **THEN** hybrid search falls back to semantic-only search
- **AND** a warning is logged indicating BM25 is disabled
- **AND** search results remain functional (semantic only)

---

### Requirement: Document Selection 3-Tier System
The system SHALL implement a 3-tier document selection system: system default → user default → conversation override.

#### Scenario: System default (all enabled)
- **WHEN** no user default or conversation override exists for a document
- **THEN** the document is enabled for search (system default = enabled)

#### Scenario: User default override
- **WHEN** a user has set a document default in `user_document_defaults`
- **THEN** that setting overrides the system default
- **AND** the setting applies to all new conversations for that user

#### Scenario: Conversation override
- **WHEN** a conversation has a document override in `conversation_document_overrides`
- **THEN** that setting overrides both system and user defaults
- **AND** the setting only applies to that specific conversation

#### Scenario: Effective selection query
- **WHEN** determining which documents are enabled for a search
- **THEN** the query uses: `COALESCE(conversation_override, user_default, TRUE)`
- **AND** only enabled, non-deleted documents are searched

---

### Requirement: Document Selection API
The system SHALL provide API endpoints for managing document selections.

#### Scenario: GET user document defaults
- **WHEN** `GET /api/user/document-defaults` is called
- **THEN** the user's document selections are returned
- **AND** documents without explicit settings show as enabled (system default)

#### Scenario: PUT user document default
- **WHEN** `PUT /api/user/document-defaults/:doc_id` is called with `{enabled: false}`
- **THEN** the user's default for that document is set to disabled
- **AND** the setting persists across conversations

#### Scenario: GET conversation document overrides
- **WHEN** `GET /api/conversations/:id/document-overrides` is called
- **THEN** the conversation-specific document overrides are returned

#### Scenario: PUT conversation document override
- **WHEN** `PUT /api/conversations/:id/document-overrides/:doc_id` is called
- **THEN** the conversation-specific override is set
- **AND** it takes precedence over user defaults for this conversation
