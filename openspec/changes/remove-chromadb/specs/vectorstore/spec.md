# Vectorstore Capability

## REMOVED Requirements

### Requirement: ChromaDB Vector Storage
The system SHALL NOT use ChromaDB for vector storage.

#### Scenario: New deployment creates no ChromaDB service
- GIVEN: A user runs `a2rchi deploy create`
- WHEN: The deployment is initialized
- THEN: No ChromaDB container is created
- AND: The compose.yaml contains only postgres and chatbot services

#### Scenario: Vector search uses PostgreSQL
- GIVEN: A deployment is running
- WHEN: A similarity search is performed
- THEN: The query executes against PostgreSQL with pgvector
- AND: No connection to ChromaDB is attempted

### Requirement: ChromaDB Configuration
The system SHALL NOT include chromadb configuration sections.

#### Scenario: Config has no chromadb section
- GIVEN: A new deployment config is generated
- WHEN: The config.yaml is created
- THEN: There is no `chromadb:` section in the config
- AND: Vectorstore settings are under `global.vectorstore`

## ADDED Requirements

### Requirement: PostgreSQL Vector Storage
The system SHALL use PostgreSQL with pgvector extension for all vector storage and similarity search.

#### Scenario: Vector embeddings stored in PostgreSQL
- GIVEN: A document is ingested
- WHEN: Embeddings are generated
- THEN: The embeddings are stored in the `document_chunks` table
- AND: The embedding column uses the pgvector `vector` type

#### Scenario: Similarity search uses pgvector
- GIVEN: A user sends a chat message
- WHEN: RAG retrieval is triggered
- THEN: Similarity search uses pgvector's cosine distance operator (`<=>`)
- AND: Results are returned ordered by similarity

### Requirement: Hybrid Search Support
The system SHALL support hybrid search combining semantic similarity with BM25 full-text search.

#### Scenario: Hybrid retrieval combines vector and keyword search
- GIVEN: A retrieval query is executed with hybrid mode
- WHEN: Documents are retrieved
- THEN: Both pgvector similarity scores and PostgreSQL full-text search ranks are considered
- AND: Results are combined using reciprocal rank fusion or weighted scoring

### Requirement: Migration from ChromaDB
The system SHALL provide a migration path for existing ChromaDB deployments.

#### Scenario: Migrate existing ChromaDB vectors
- GIVEN: An existing deployment with ChromaDB vectors
- WHEN: The migration command is run
- THEN: All vectors are copied to PostgreSQL `document_chunks` table
- AND: Document metadata is preserved
- AND: The migration reports success with vector counts

## MODIFIED Requirements

### Requirement: Vectorstore Configuration
The system SHALL configure vectorstore settings under `global.vectorstore` with PostgreSQL as the only backend.

#### Scenario: Default vectorstore config
- GIVEN: A new deployment is created
- WHEN: The default config is generated
- THEN: `global.vectorstore.type` is set to `postgres`
- AND: `global.vectorstore.collection_name` defaults to `default`
- AND: `global.vectorstore.distance_metric` defaults to `cosine`
