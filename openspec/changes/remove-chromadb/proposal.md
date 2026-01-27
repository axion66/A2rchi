# Proposal: Remove ChromaDB and Consolidate on PostgreSQL

## Summary
Remove ChromaDB as a dependency and service, consolidating all vector storage, full-text search, and configuration management on PostgreSQL with pgvector extension.

## Motivation
- **Reduced Complexity**: One database service instead of two reduces operational overhead
- **Better Integration**: pgvector provides native SQL integration with vectors, enabling complex queries combining vector similarity with relational filters
- **Existing Implementation**: `PostgresVectorStore` is already implemented and feature-complete
- **Cost Efficiency**: One database to maintain, backup, and monitor
- **BM25 Support**: PostgreSQL's full-text search provides BM25 ranking natively
- **Hybrid Search**: Easier to combine semantic + keyword search in a single query

## Scope

### In Scope
1. Remove ChromaDB service from Docker Compose templates
2. Remove ChromaDB Dockerfile
3. Update VectorStoreManager to use PostgresVectorStore exclusively
4. Update config templates to remove chromadb section
5. Update CLI service builder to not create chromadb service
6. Remove chromadb from requirements
7. Update example configs
8. Update documentation
9. Provide migration path for existing deployments

### Out of Scope
- Changes to embedding models or dimensions
- Changes to retrieval algorithms (beyond backend switch)
- Changes to the chat interface

## Technical Approach

### Database Schema
The `init-v2.sql` already includes the necessary tables:
- `document_chunks` - stores embeddings with pgvector
- `documents` - document metadata
- Full-text search indexes for BM25

### Migration Strategy
For existing deployments with ChromaDB data:
1. Use `MigrationManager.migrate_chromadb()` to copy vectors to PostgreSQL
2. Verify data integrity
3. Stop and remove ChromaDB container
4. Update config to use postgres vectorstore

### Affected Components

| Component | Change |
|-----------|--------|
| `src/cli/templates/base-compose.yaml` | Remove chromadb service |
| `src/cli/templates/base-config.yaml` | Remove chromadb section, add postgres vectorstore |
| `src/cli/templates/dockerfiles/Dockerfile-chroma` | Delete |
| `src/cli/utils/service_builder.py` | Remove chromadb service creation |
| `src/data_manager/vectorstore/manager.py` | Use PostgresVectorStore only |
| `examples/deployments/*/config.yaml` | Update all example configs |
| `requirements/requirements-base.txt` | Remove chromadb dependency |
| `docs/` | Update documentation |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Data loss during migration | Migration manager validates counts before/after |
| Performance regression | pgvector HNSW index provides comparable performance |
| Breaking existing deployments | Provide migration guide and CLI command |

## Success Criteria
- [ ] All tests pass without ChromaDB
- [ ] New deployments work with PostgreSQL-only vector store
- [ ] Migration path documented and tested
- [ ] No references to chromadb in source code (except migration tools)

## Timeline
- Estimated effort: 4-6 hours
- No external dependencies
