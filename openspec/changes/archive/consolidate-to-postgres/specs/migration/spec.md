## ADDED Requirements

### Requirement: Migration CLI Command
The system SHALL provide an `a2rchi migrate` CLI command to migrate from ChromaDB/SQLite to PostgreSQL-only storage.

#### Scenario: Migration command invocation
- **WHEN** `a2rchi migrate <deployment> --from-chromadb` is called
- **THEN** the migration process begins
- **AND** progress is logged to stdout
- **AND** errors are logged to stderr with clear descriptions

#### Scenario: Pre-migration validation
- **WHEN** migration starts
- **THEN** it verifies PostgreSQL 17+ is available
- **AND** it verifies required extensions are installed
- **AND** it checks that source data (SQLite, ChromaDB) exists
- **AND** it fails early with clear errors if validation fails

---

### Requirement: Catalog Migration
**STATUS: ✅ DONE (PR #404)** - New documents are stored in PostgreSQL. Legacy SQLite data is not migrated (deprecated approach).

The system no longer requires migration from SQLite `catalog.sqlite` to PostgreSQL. New data goes directly to the `resources` table.

---

### Requirement: Embeddings Migration
The system SHALL migrate vector embeddings from ChromaDB to PostgreSQL `document_chunks` table.

#### Scenario: Chunk and embedding migration
- **WHEN** migrating ChromaDB data
- **THEN** all chunks are copied with their embeddings to `document_chunks`
- **AND** chunk_text, embedding vector, and metadata are preserved
- **AND** document_id foreign key is set based on resource_hash

#### Scenario: Re-embedding fallback
- **WHEN** ChromaDB embeddings cannot be directly migrated (format incompatibility)
- **THEN** the migration re-embeds documents using the configured embedding model
- **AND** progress is shown (e.g., "Embedding document 47/150")

#### Scenario: Vector dimension validation
- **WHEN** migrating embeddings
- **THEN** the migration verifies embedding dimensions match static_config.embedding_dimensions
- **AND** mismatched dimensions cause migration to fail with clear error

---

### Requirement: Document Selection Migration
The system SHALL migrate document selection state from chat_document_selections to `user_document_defaults`.

#### Scenario: Selection state migration
- **WHEN** migrating document selections
- **THEN** user-specific document disabled states are copied to `user_document_defaults`
- **AND** conversation-specific overrides are copied to `conversation_document_overrides`

---

### Requirement: Migration Rollback
The system SHALL support rollback of failed migrations.

#### Scenario: Chunked migration with checkpoints
- **WHEN** migrating large datasets (>1000 documents)
- **THEN** migration proceeds in batches (e.g., 100 documents per batch)
- **AND** progress is checkpointed after each batch to a migration_state table
- **AND** failed migration can resume from last checkpoint with `--resume` flag

#### Scenario: Automatic rollback on failure
- **WHEN** migration fails partway through a batch
- **THEN** the current batch transaction is rolled back
- **AND** previously committed batches remain intact
- **AND** error message indicates what failed and suggests `--resume` to continue

#### Scenario: Manual rollback
- **WHEN** `a2rchi migrate <deployment> --rollback` is called
- **THEN** the PostgreSQL data is cleared
- **AND** original SQLite/ChromaDB data remains intact
- **AND** a success message indicates rollback completed

#### Scenario: Dry run preview
- **WHEN** `a2rchi migrate <deployment> --from-chromadb --dry-run` is called
- **THEN** migration is validated without making changes
- **AND** estimated document count and time are displayed
- **AND** any potential issues are reported

---

### Requirement: Migration Downtime Documentation
The system documentation SHALL clearly state expected migration downtime.

#### Scenario: Downtime estimates in documentation
- **WHEN** a user reads migration documentation
- **THEN** expected downtime is documented:
  - Small (< 100 docs): ~2-5 minutes
  - Medium (100-1000 docs): ~10-30 minutes
  - Large (1000+ docs): ~1-2 hours

#### Scenario: Pre-migration checklist
- **WHEN** a user prepares to migrate
- **THEN** documentation provides a checklist:
  - Backup existing data
  - Verify PostgreSQL 17+ availability
  - Estimate downtime based on document count
  - Schedule maintenance window
