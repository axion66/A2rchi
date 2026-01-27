# Proposal: Unified Config Management

## Problem Statement

A2rchi currently has fragmented configuration handling:

1. **config_loader.py** - File-based YAML loading used by 22+ files
2. **ConfigService** - PostgreSQL-based static/dynamic config (new, underutilized)
3. **ConfigurationManager** - CLI-specific config merging/validation
4. **SecretsManager** - Environment variable and secrets handling

This creates:
- Inconsistent config access patterns across codebase
- No clear ownership of config initialization
- Difficult to add runtime config changes
- Services load config differently (some direct YAML, some via loader)

## Proposed Solution

Unify configuration management around ConfigService while maintaining backward compatibility:

### 1. Config Layers
```
┌─────────────────────────────────────┐
│  User Preferences (per-user)        │  ← users table
├─────────────────────────────────────┤
│  Runtime (Dynamic)                  │  ← dynamic_config table
├─────────────────────────────────────┤
│  Deploy-time (Static)               │  ← static_config table
├─────────────────────────────────────┤
│  config.yaml files                  │  ← Source of truth for deployment
└─────────────────────────────────────┘
```

---

## Configuration Categories

### STATIC (Set at Deployment Time)
*Changing these requires redeployment/restart/reindexing*

| Category | Settings | Rationale |
|----------|----------|-----------|
| **Identity** | `deployment_name`, `config_version` | Container names, volumes, schema |
| **Paths** | `data_path`, `accounts_path`, `accepted_files` | Volume mounts, file structure |
| **Embedding** | `embedding_model`, `embedding_dimensions`, `embedding_class_map` | Changing invalidates ALL vectors |
| **Chunking** | `chunk_size`, `chunk_overlap` | Requires full re-index |
| **Database** | `postgres.host/port/user/database` | Connection strings |
| **Networking** | `services.*.port`, `services.*.external_port`, `services.*.host` | Container port bindings |
| **Auth Config** | `auth.enabled`, `auth.sso.*`, `auth.basic.enabled` | Architecture choice |
| **Available Models** | `model_class_map` (model definitions) | What's installed |
| **Available Pipelines** | `pipeline_map` (pipeline definitions) | What's available |
| **Security Flags** | `flask_debug_mode`, `enable_debug_endpoints` | Security sensitive |
| **Data Sources** | `sources.*.enabled`, `sources.*.paths/urls` | What to ingest |
| **Integrations** | `piazza.network_id`, `redmine.*`, `mattermost.*` | External system config |

### DYNAMIC (Changeable at Runtime via API)
*Can be changed without restart*

| Category | Settings | Default | Notes |
|----------|----------|---------|-------|
| **Active Selection** | `active_pipeline` | `QAPipeline` | Which pipeline to use |
| | `active_model` | `openai/gpt-4o` | Default model for chat |
| **Generation** | `temperature` | `0.7` | LLM temperature |
| | `max_tokens` | `4096` | Max response length |
| | `top_p` | `0.9` | Nucleus sampling |
| | `top_k` | `50` | Top-k sampling |
| | `repetition_penalty` | `1.0` | Repetition control |
| **Prompts** | `system_prompt` | `null` | Global system prompt |
| | `condense_prompt` | (pipeline default) | Question condensation |
| | `chat_prompt` | (pipeline default) | Chat response prompt |
| **Retrieval** | `num_documents_to_retrieve` | `10` | RAG document count |
| | `use_hybrid_search` | `true` | Semantic + BM25 |
| | `bm25_weight` | `0.3` | Hybrid balance |
| | `semantic_weight` | `0.7` | Hybrid balance |
| | `bm25_k1` | `1.2` | Term frequency saturation |
| | `bm25_b` | `0.75` | Length normalization |
| **Schedules** | `sources.*.schedule` | `""` | Ingestion cron schedules |
| | `piazza.update_time` | `60` | Polling interval (seconds) |
| | `mattermost.update_time` | `60` | Polling interval (seconds) |
| **Logging** | `verbosity` | `3` | Log level (1-5) |
| **UI/UX** | `num_responses_until_feedback` | `3` | Feedback prompt frequency |
| | `include_copy_button` | `false` | UI toggle |

### USER PREFERENCES (Per-User, Override Dynamic)
*Stored in `users` table*

| Setting | Column | Notes |
|---------|--------|-------|
| `theme` | `theme` | `'light'`, `'dark'`, `'system'` |
| `preferred_model` | `preferred_model` | Overrides `active_model` |
| `preferred_temperature` | `preferred_temperature` | Overrides `temperature` |
| **BYOK Keys** | `api_key_openai` | Encrypted with pgcrypto |
| | `api_key_anthropic` | Encrypted |
| | `api_key_openrouter` | Encrypted |

---

## Success Criteria

- [ ] All services use ConfigService for config access
- [ ] Runtime settings changeable via API (no restart)
- [ ] User preferences override system defaults
- [ ] Model class mapping cleanly separated from config loading
- [ ] config_loader.py deprecated and removed
- [ ] No breaking changes to CLI or deployment flow

## Scope

### In Scope
- Unify config access patterns
- Runtime config modification API
- Model/embedding class registry
- Service dependency injection
- Prompt management (dynamic)

### Out of Scope
- Multi-tenant config isolation
- Config versioning/history
- Config validation UI

## Questions to Resolve

1. Should ConfigService require PostgreSQL at startup, or support YAML-only mode?
2. How to handle model class mapping (currently done in config_loader)?
3. Should we keep backwards-compatible `load_config()` as thin wrapper?
