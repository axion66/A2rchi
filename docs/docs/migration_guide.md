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

## Migration Prerequisites

1. **Backup your data** before migrating
2. Ensure PostgreSQL 17+ is running with pgvector extension
3. Have your deployment name ready (e.g., `mybot`)

## Migration Commands

### Dry Run (Recommended First)

Check what would be migrated without making changes:

```bash
a2rchi migrate --name mybot --dry-run
```

This shows:
- Number of ChromaDB vectors to migrate
- Number of SQLite catalog records
- Estimated migration time

### Full Migration

Migrate all data sources:

```bash
a2rchi migrate --name mybot
```

### Selective Migration

Migrate specific data sources:

```bash
# Migrate only ChromaDB vectors
a2rchi migrate --name mybot --source chromadb

# Migrate only SQLite catalog
a2rchi migrate --name mybot --source sqlite

# Clean up old configs table (after verifying new schema works)
a2rchi migrate --name mybot --source configs
```

### Migration Options

| Option | Description |
|--------|-------------|
| `--source` | Data source: `chromadb`, `sqlite`, `configs`, or `all` (default) |
| `--dry-run` | Analyze without making changes |
| `--batch-size` | Records per batch (default: 1000) |
| `--verbosity` | Logging verbosity 0-4 (default: 3) |

## What Gets Migrated

### ChromaDB → pgvector

- All document embeddings and text chunks
- Metadata (source, filename, chunk_index, etc.)
- Preserved document hashes for deduplication

### SQLite Catalog → documents table

- Document sources and URLs
- File hashes and metadata
- Source configuration

### Conversation Schema Updates

The conversation schema is updated from:
- `conf_id` (foreign key to configs table)

To:
- `model_used` (string, e.g., "openai/gpt-4o")
- `pipeline_used` (string, e.g., "QAPipeline")

## Post-Migration Steps

1. **Verify the migration**:
   ```bash
   a2rchi migrate --name mybot --dry-run
   # Should show "Nothing to migrate!"
   ```

2. **Test your deployment**:
   ```bash
   a2rchi up --name mybot
   ```

3. **Clean up old data** (optional, after verification):
   - ChromaDB volume can be removed
   - SQLite catalog file can be removed

## Troubleshooting

### Migration Fails Midway

Migrations are resumable. Simply run the same command again:

```bash
a2rchi migrate --name mybot
```

The migration will resume from the last checkpoint.

### ChromaDB Not Found

If you get "ChromaDB not found, skipping":
- This is normal if you don't have existing ChromaDB data
- Or the data path may be incorrect in your config

### PostgreSQL Connection Errors

Ensure:
1. PostgreSQL is running: `docker ps | grep postgres`
2. Password is set in secrets: `cat ~/.a2rchi/a2rchi-mybot/secrets/PG_PASSWORD`
3. Database exists: `a2rchi-db`

## New Deployments

New deployments automatically use the consolidated PostgreSQL schema. No migration needed.

```bash
# Create a new PostgreSQL-only deployment
a2rchi create --name mynewbot --config myconfig.yaml
a2rchi up --name mynewbot
```

## Schema Reference

The new schema (init-v2.sql) includes:

- `users` - User accounts with BYOK API keys
- `static_config` - Deploy-time configuration
- `dynamic_config` - Runtime-modifiable settings
- `document_chunks` - Vector embeddings with pgvector
- `documents` - Document catalog
- `resources` - Raw resource tracking
- `conversation_metadata` - Conversation headers
- `conversations` - Message history with model/pipeline tracking

See `src/cli/templates/init-v2.sql` in the repository for the complete schema.
