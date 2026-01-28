# Migration Guide: PostgreSQL Consolidation

This guide covers migrating existing A2rchi deployments to the consolidated PostgreSQL storage architecture.

## Overview

A2rchi v2.0 consolidates all storage to PostgreSQL:

| Component | Before (v1.x) | After (v2.0) |
|-----------|---------------|--------------|
| Vector Storage | ChromaDB | PostgreSQL + pgvector |
| Document Catalog | SQLite | PostgreSQL |
| Conversations | PostgreSQL | PostgreSQL (updated schema) |
| Configuration | YAML files | YAML files (unchanged) |

## Migration Strategy: Reingest

**There is no automatic data migration tool.** The recommended approach is to:

1. Create a fresh v2.0 deployment
2. Re-ingest your documents from source
3. Start conversations fresh (history is not migrated)

This is the cleanest approach because:
- Document embeddings should be regenerated with consistent settings
- The new schema structure differs significantly from v1.x
- Re-ingesting ensures data integrity

## Migration Steps

### 1. Backup Existing Deployment (Optional)

If you want to preserve your v1.x data:

```bash
# Backup ChromaDB data
cp -r ~/.a2rchi/a2rchi-mybot/chromadb ~/.a2rchi/a2rchi-mybot/chromadb.backup

# Export PostgreSQL conversations (if you want to keep history)
pg_dump -h localhost -p 5432 -U a2rchi -t conversations a2rchi_db > conversations_backup.sql
```

### 2. Create New v2.0 Deployment

```bash
# Delete old deployment
a2rchi delete --name mybot

# Create fresh deployment with your existing config
a2rchi create --name mybot --config myconfig.yaml
```

### 3. Re-ingest Documents

```bash
# Start the deployment
a2rchi up --name mybot

# The data manager will re-ingest documents from configured sources
# Check the logs to monitor progress
docker logs a2rchi-mybot-data-manager -f
```

### 4. Verify Deployment

```bash
# Open the chat UI
open http://localhost:7861

# Test a query to verify documents are indexed
```

## What Changes

### New Storage Schema

The new schema (init-v2.sql) includes:

- `users` - User accounts with BYOK API keys
- `static_config` - Deploy-time configuration
- `dynamic_config` - Runtime-modifiable settings
- `document_chunks` - Vector embeddings with pgvector
- `documents` - Document catalog
- `resources` - Raw resource tracking
- `conversation_metadata` - Conversation headers
- `conversations` - Message history with model/pipeline tracking

### Conversation Schema

Conversations now track:
- `model_used` (string, e.g., "openai/gpt-4o")
- `pipeline_used` (string, e.g., "QAPipeline")

Instead of the previous `conf_id` foreign key.

## New Deployments

New deployments automatically use the consolidated PostgreSQL schema:

```bash
a2rchi create --name mynewbot --config myconfig.yaml
a2rchi up --name mynewbot
```

## Troubleshooting

### PostgreSQL Connection Errors

Ensure:
1. PostgreSQL is running: `docker ps | grep postgres`
2. Password is set in secrets: `cat ~/.a2rchi/a2rchi-mybot/secrets/PG_PASSWORD`
3. Database exists: `a2rchi-db`

### Documents Not Appearing

Check data manager logs:
```bash
docker logs a2rchi-mybot-data-manager -f
```

Common issues:
- Source paths not accessible from container
- Network issues reaching web sources
- Embedding model not available

## Schema Reference

See `src/cli/templates/init-v2.sql` in the repository for the complete PostgreSQL schema.

---

## Future: Automated Migration (Planned)

An automated migration tool (`a2rchi migrate`) is planned for a future release to support:
- ChromaDB → pgvector vector migration
- SQLite catalog → PostgreSQL documents table
- Conversation history preservation

Until then, the reingest approach above is recommended.
