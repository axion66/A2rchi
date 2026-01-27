# Design: Unified Config Management

## Context

A2rchi configuration is currently spread across:
- `config.yaml` files (22+ files import config_loader)
- `ConfigService` (PostgreSQL-based, underutilized)
- Environment variables / secrets
- Prompt files (`.prompt` files)

### Constraints
- PostgreSQL is required for all runtime operations
- Prompt files should remain version-controllable
- Model class mapping requires Python imports
- Clean break from legacy config_loader (no backward compat)

### Stakeholders
- **Admins**: Manage deployment-wide settings
- **Users**: Personal preferences that override defaults
- **Developers**: Need clean config access patterns

## Goals / Non-Goals

### Goals
- Single entry point for config access (`ConfigService`)
- PostgreSQL-only operation (no YAML fallback mode)
- Three-tier config: static → deployment dynamic → user preferences
- Admin-only access for deployment-level changes
- Prompt files remain as files (dynamic selection, static content)

### Non-Goals
- Backward compatibility with config_loader
- YAML-only mode
- Web UI for config editing (future work)

## Key Decisions

### 1. PostgreSQL-Only Operation

ConfigService requires PostgreSQL. Period.

```python
class ConfigService:
    def __init__(self, pg_config: Dict[str, Any]):
        """PostgreSQL config required."""
        self._pg_config = pg_config
        # No YAML fallback
```

**CLI commands** that run before PostgreSQL exists (like `a2rchi init`) read YAML directly - they don't use ConfigService. ConfigService is for runtime services only.

**Rationale**: Simplicity. One code path, one source of truth at runtime.

### 2. Three-Tier Config Hierarchy

```
┌─────────────────────────────────────┐
│  User Preferences (per-user)        │  ← users table (any authenticated user)
├─────────────────────────────────────┤
│  Deployment Dynamic (per-deploy)    │  ← dynamic_config table (admin only)
├─────────────────────────────────────┤
│  Static (deploy-time)               │  ← static_config table (immutable)
└─────────────────────────────────────┘
```

**Effective value resolution:**
```python
def get_effective_temperature(user_id: str) -> float:
    # 1. Check user preference
    user = get_user(user_id)
    if user.preferred_temperature is not None:
        return user.preferred_temperature
    
    # 2. Fall back to deployment default
    dynamic = get_dynamic_config()
    return dynamic.temperature
```

### 3. Admin-Only Deployment Settings

Deployment-wide dynamic config requires admin role:

```python
class ConfigService:
    def update_dynamic_config(self, updates: Dict, user_id: str) -> DynamicConfig:
        """Update deployment-wide dynamic config. Admin only."""
        if not self._is_admin(user_id):
            raise PermissionError("Only admins can update deployment config")
        
        # ... perform update
        self._log_audit(user_id, updates)
```

**Users table gets admin flag:**
```sql
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;
```

**API authorization:**
```
PUT /api/v2/config/dynamic          # 403 unless admin
PUT /api/v2/user/preferences        # Any authenticated user (their own)
```

### 4. Prompt Management

Prompts stay as **files**, with dynamic **selection**:

```
/root/A2rchi/prompts/
├── condense/
│   ├── default.prompt
│   └── concise.prompt
├── chat/
│   ├── default.prompt
│   ├── formal.prompt
│   └── technical.prompt
└── system/
    ├── default.prompt
    └── custom.prompt
```

**Deployment config stores the default selection (admin):**
```sql
-- In dynamic_config table
active_condense_prompt VARCHAR(100) DEFAULT 'default',
active_chat_prompt VARCHAR(100) DEFAULT 'default', 
active_system_prompt VARCHAR(100) DEFAULT 'default',
```

**Users can override prompt selection:**
```sql
-- In users table
preferred_condense_prompt VARCHAR(100),  -- NULL = use deployment default
preferred_chat_prompt VARCHAR(100),
preferred_system_prompt VARCHAR(100),
```

**Reload via explicit API call:**
```
POST /api/v2/prompts/reload         # Admin only, reloads prompt cache
```

**Rationale**: 
- Prompt content is version-controllable (git)
- Selection is runtime-changeable at deployment or user level
- Explicit reload prevents unexpected behavior

### 5. Model Class Registry

Separate model class mapping from config:

```python
# src/a2rchi/models/registry.py
class ModelRegistry:
    """Maps model names to classes. Singleton."""
    
    _models: Dict[str, Type] = {
        "AnthropicLLM": AnthropicLLM,
        "OpenAILLM": OpenAILLM,
        "DumbLLM": DumbLLM,
        # ...
    }
    
    @classmethod
    def get(cls, name: str) -> Type:
        return cls._models[name]
```

**Config stores model kwargs, not classes:**
```yaml
# In static_config (what's available)
available_models:
  - id: "openai/gpt-4o"
    class: "OpenAILLM"
    default_kwargs: {model_name: "gpt-4o", temperature: 0.7}
  - id: "anthropic/claude-3"
    class: "AnthropicLLM"  
    default_kwargs: {model_name: "claude-3-opus", temperature: 0.7}
```

### 6. Schema Changes

#### Users Table (add admin + preferences)
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_condense_prompt VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_chat_prompt VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_system_prompt VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_max_tokens INTEGER;
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_num_documents INTEGER;
```

#### Dynamic Config (deployment-level, admin only)
```sql
ALTER TABLE dynamic_config ADD COLUMN IF NOT EXISTS
    -- Prompt selection (not content)
    active_condense_prompt VARCHAR(100) DEFAULT 'default',
    active_chat_prompt VARCHAR(100) DEFAULT 'default',
    active_system_prompt VARCHAR(100) DEFAULT 'default',
    
    -- Model generation params
    top_p NUMERIC(3,2) DEFAULT 0.9,
    top_k INTEGER DEFAULT 50,
    repetition_penalty NUMERIC(4,2) DEFAULT 1.0,
    
    -- Schedules (cron expressions)
    ingestion_schedule VARCHAR(100) DEFAULT '',
    
    -- Logging
    verbosity INTEGER DEFAULT 3;
```

#### Config Audit (track admin changes)
```sql
CREATE TABLE IF NOT EXISTS config_audit (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(200) NOT NULL REFERENCES users(id),
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    config_type VARCHAR(20) NOT NULL,  -- 'dynamic', 'user_pref'
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT
);
```

### 7. Config Access Pattern

**Remove config_loader.py entirely.** All services use ConfigService:

```python
from src.utils import ConfigService, ModelRegistry

class ChatService:
    def __init__(self, config_service: ConfigService):
        self._config = config_service
    
    def get_response(self, user_id: str, message: str):
        # Get effective config for this user
        temperature = self._config.get_effective("temperature", user_id)
        model_id = self._config.get_effective("active_model", user_id)
        
        model_class = ModelRegistry.get(model_id)
        # ...
```

### 8. Static Config Initialization

On first startup, static config is populated from config.yaml:

```python
class ConfigService:
    def initialize_static_config(self, yaml_config: Dict) -> None:
        """Called once during deployment initialization."""
        # Extract static values from YAML
        static = StaticConfig(
            deployment_name=yaml_config["name"],
            data_path=yaml_config["global"]["DATA_PATH"],
            embedding_model=yaml_config["data_manager"]["embedding_name"],
            # ...
        )
        self._write_static_config(static)
```

This happens during `a2rchi start` (not in ConfigService itself).

## Dependencies

This proposal depends on:
- **auth-system**: Provides `@admin_required`, `@login_required`, user identity

## Migration Plan

### Phase 1: Foundation
- [ ] Create `ModelRegistry` class
- [ ] Create prompts directory structure  
- [ ] Update schema (users.is_admin, dynamic_config fields, config_audit)
- [ ] Add `is_admin` check to ConfigService

### Phase 2: ConfigService Enhancement
- [ ] Add `get_effective(field, user_id)` method
- [ ] Add audit logging for changes
- [ ] Add prompt file loading + cache

### Phase 3: Service Migration (Big Bang)
- [ ] Remove all `from src.utils.config_loader import` statements (22+ files)
- [ ] Update services to receive ConfigService via DI
- [ ] Delete config_loader.py
- [ ] Single PR, all changes land together

### Phase 4: API & Docs
- [ ] Add admin-only middleware for deployment config endpoints
- [ ] Update API docs
- [ ] Update user guide

## API Endpoints

### Deployment Config (Admin Only)
```
GET  /api/v2/config/dynamic           # Get deployment dynamic settings
PUT  /api/v2/config/dynamic           # Update (admin only, audited)
```

### Static Config (Read Only)
```
GET  /api/v2/config/static            # Get static config
```

### User Preferences (Own User)
```
GET  /api/v2/user/preferences         # Get own preferences
PUT  /api/v2/user/preferences         # Update own preferences
```

### Prompts
```
GET  /api/v2/prompts                  # List available prompts by type
GET  /api/v2/prompts/:type/:name      # Get prompt content
POST /api/v2/prompts/reload           # Reload prompt cache (admin only)
```

## Resolved Decisions

| Question | Decision |
|----------|----------|
| Migration strategy | Big bang - single PR with all changes |
| Auth disabled scenario | Auth is always enabled (separate proposal for proper auth) |
| CLI commands needing ConfigService | Only running services use ConfigService. CLI (`init`, `start`, `restart`, `stop`, `status`) reads YAML directly for deployment config |
| Testing strategy | Use PostgreSQL (testcontainers or similar) |
| User-overridable settings | All non-security settings (model, temperature, top_p, top_k, prompts, num_documents, etc.) |
| Prompts path | Configurable via `static_config.prompts_path` |
| BYOK key errors | Surface error to user ("Your API key for X is invalid") |
| Static config re-sync | Re-sync from YAML on every `a2rchi start` (allows config updates) |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Breaking all config_loader usages (22+ files) | Big bang migration, thorough testing |
| Large PR hard to review | Clear commit structure, comprehensive tests |
| Prompt file permissions in containers | Document volume mount requirements |
| Auth complexity | Separate proposal for proper auth library integration |

## Out of Scope (Future Work)

- **Auth system overhaul**: Current design assumes auth exists. Needs separate proposal for proper auth library (OAuth2, OIDC, etc.)
- **Config UI**: Web interface for editing config
- **Config versioning**: History beyond audit log

## File Deletions

The following files will be **removed**:
- `src/utils/config_loader.py` - Replaced by ConfigService
