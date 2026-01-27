## ADDED Requirements

### Requirement: PostgreSQL Database Schema
The system SHALL use a single PostgreSQL 17+ database with pgvector, pg_textsearch, pgcrypto, and pg_trgm extensions for all persistent storage.

#### Scenario: Database initialization
- **WHEN** the PostgreSQL container starts for the first time
- **THEN** init.sql creates all tables, indexes, and extensions
- **AND** the `static_config` table is populated from config.yaml
- **AND** the `dynamic_config` table is initialized with defaults

#### Scenario: Extension availability
- **WHEN** querying the database
- **THEN** pgvector, pg_textsearch, pgcrypto, and pg_trgm extensions are available

---

### Requirement: Connection Pool Management
The system SHALL use a connection pool for PostgreSQL connections to ensure efficient resource usage.

#### Scenario: Connection reuse
- **WHEN** multiple requests need database access
- **THEN** connections are reused from a pool
- **AND** pool size is configurable (default: 5 min, 20 max)

#### Scenario: Connection timeout handling
- **WHEN** a connection cannot be acquired within timeout
- **THEN** an appropriate error is raised
- **AND** the request fails gracefully with a 503 response

---

### Requirement: Users Table
The system SHALL maintain a `users` table for identity, preferences, and BYOK API keys.

#### Scenario: User creation on first interaction
- **WHEN** a new user_id interacts with the system
- **THEN** a row is created in the `users` table with default preferences
- **AND** auth_provider is set based on authentication method

#### Scenario: Anonymous user identification
- **WHEN** an unauthenticated user interacts with the system
- **THEN** a user_id is generated from client session/cookie
- **AND** auth_provider is set to 'anonymous'
- **AND** the user can later be linked to an authenticated identity

#### Scenario: BYOK API key storage
- **WHEN** a user provides an API key for a provider
- **THEN** the key is encrypted using pgcrypto `pgp_sym_encrypt()`
- **AND** stored in the appropriate `api_key_*` column
- **AND** decrypted on read using `pgp_sym_decrypt()`

#### Scenario: User preferences persistence
- **WHEN** a user updates their preferences (theme, preferred_model)
- **THEN** the changes are persisted to the `users` table
- **AND** `updated_at` timestamp is set

---

### Requirement: Document Catalog in PostgreSQL
**STATUS: ✅ DONE (PR #404)** - CatalogService now uses PostgreSQL `resources` table.

The system SHALL store document catalog metadata in the `resources` table, replacing SQLite catalog.sqlite.

#### Scenario: Document ingestion
- **WHEN** a new document is ingested
- **THEN** metadata is stored in the `resources` table with resource_hash as unique key
- **AND** file content remains on the filesystem (not in database)

#### Scenario: Document lookup by hash
- **WHEN** looking up a document by resource_hash
- **THEN** the system returns document metadata from the `resources` table

> **Note:** Soft delete (`is_deleted` flag) was deferred from initial implementation.

---

### Requirement: Document Chunks with Embeddings
The system SHALL store document chunks and their vector embeddings in the `document_chunks` table, replacing ChromaDB.

#### Scenario: Chunk storage with embedding
- **WHEN** a document is chunked and embedded
- **THEN** each chunk is stored with chunk_text, embedding vector, and metadata
- **AND** chunk_index maintains ordering within the document

#### Scenario: Vector index creation
- **WHEN** the database is initialized with vector_index.type = "hnsw"
- **THEN** an HNSW index is created on the embedding column
- **AND** index parameters (m, ef_construction) are configurable

#### Scenario: BM25 index creation
- **WHEN** the database is initialized
- **THEN** a BM25 index is created on chunk_text using pg_textsearch
- **AND** k1 and b parameters are configurable

---

### Requirement: Conversation Tracking with Model Info
The system SHALL record which model and pipeline were used for each message in the `conversations` table.

#### Scenario: Message insertion with model tracking
- **WHEN** a message is inserted into the conversations table
- **THEN** `model_used` and `pipeline_used` columns are populated
- **AND** this replaces the previous `conf_id` foreign key to configs table

#### Scenario: Grafana analytics compatibility
- **WHEN** querying conversation analytics
- **THEN** `model_used` column provides the model identifier
- **AND** no join to configs table is required

---

### Requirement: A/B Comparison Without Config Table
The system SHALL track A/B comparisons using model_a/model_b columns instead of config foreign keys.

#### Scenario: A/B comparison creation
- **WHEN** an A/B comparison is created
- **THEN** `model_a` and `model_b` columns store model identifiers
- **AND** `pipeline_a` and `pipeline_b` columns store pipeline identifiers
- **AND** no foreign key to configs table exists

---

### Requirement: Grafana Read-Only Access
The system SHALL provide a read-only PostgreSQL user for Grafana dashboards.

#### Scenario: Grafana user permissions
- **WHEN** the Grafana user connects
- **THEN** it has SELECT permission on all tables
- **AND** it cannot INSERT, UPDATE, or DELETE

#### Scenario: Dashboard query migration
- **WHEN** existing Grafana dashboards query conversation data
- **THEN** they use `conversations.model_used` instead of joining to configs table
