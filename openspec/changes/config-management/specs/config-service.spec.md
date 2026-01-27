# Spec: Configuration Service

## Overview
Unified configuration management with three-tier hierarchy: static (deploy-time), dynamic (admin-controlled), and user preferences.

---

## ADDED Requirements

### Requirement: Static Configuration
The system SHALL store immutable deploy-time configuration in PostgreSQL.

#### Scenario: Static config initialization
- **GIVEN** a config.yaml file exists
- **WHEN** `a2rchi start` runs for the first time
- **THEN** static_config table is populated from config.yaml
- **AND** subsequent starts re-sync from config.yaml (allows updates)

#### Scenario: Static config access
- **WHEN** a service requests static configuration
- **THEN** ConfigService returns cached StaticConfig object
- **AND** no database query is made after initial load

#### Scenario: Static config is immutable at runtime
- **WHEN** attempting to modify static_config via API
- **THEN** the request is rejected with 405 Method Not Allowed

---

### Requirement: Dynamic Configuration (Deployment-Level)
The system SHALL allow admins to modify deployment-wide settings at runtime.

#### Scenario: Get dynamic config
- **GIVEN** an authenticated user
- **WHEN** GET /api/v2/config/dynamic
- **THEN** response is 200 with current dynamic settings

#### Scenario: Update dynamic config as admin
- **GIVEN** an admin user is authenticated
- **WHEN** PUT /api/v2/config/dynamic with {temperature: 0.5}
- **THEN** dynamic_config is updated
- **AND** config_audit record is created
- **AND** response is 200 with updated config

#### Scenario: Update dynamic config as non-admin
- **GIVEN** a non-admin user is authenticated
- **WHEN** PUT /api/v2/config/dynamic
- **THEN** response is 403 with {error: "Admin access required"}

#### Scenario: Config audit logging
- **WHEN** an admin updates dynamic config
- **THEN** config_audit records: user_id, field_name, old_value, new_value, changed_at

---

### Requirement: User Preferences
The system SHALL allow users to override dynamic settings with personal preferences.

#### Scenario: Get user preferences
- **GIVEN** an authenticated user
- **WHEN** GET /api/v2/user/preferences
- **THEN** response is 200 with their preferences (may include nulls)

#### Scenario: Update user preferences
- **GIVEN** an authenticated user
- **WHEN** PUT /api/v2/user/preferences with {preferred_model: "anthropic/claude-3"}
- **THEN** their preferences are updated
- **AND** response is 200

#### Scenario: Anonymous user cannot access preferences
- **GIVEN** an anonymous user
- **WHEN** GET /api/v2/user/preferences
- **THEN** response is 401

---

### Requirement: Effective Configuration Resolution
The system SHALL resolve effective config values with precedence: user > dynamic > static.

#### Scenario: User preference overrides dynamic
- **GIVEN** dynamic_config.temperature = 0.7
- **AND** user.preferred_temperature = 0.3
- **WHEN** get_effective("temperature", user_id) is called
- **THEN** returns 0.3

#### Scenario: Dynamic used when no user preference
- **GIVEN** dynamic_config.active_model = "openai/gpt-4o"
- **AND** user.preferred_model is NULL
- **WHEN** get_effective("active_model", user_id) is called
- **THEN** returns "openai/gpt-4o"

#### Scenario: Anonymous user gets dynamic defaults
- **GIVEN** an anonymous user (g.is_anonymous = True)
- **WHEN** get_effective("temperature", anon_user_id) is called
- **THEN** returns dynamic_config.temperature (no user lookup)

---

### Requirement: Prompt File Management
The system SHALL manage prompts as files with dynamic selection.

#### Scenario: List available prompts
- **WHEN** GET /api/v2/prompts
- **THEN** response lists prompt types and available prompts per type
```json
{
  "condense": ["default", "concise"],
  "chat": ["default", "formal", "technical"],
  "system": ["default"]
}
```

#### Scenario: Get prompt content
- **WHEN** GET /api/v2/prompts/chat/formal
- **THEN** response is 200 with prompt content

#### Scenario: Get non-existent prompt
- **WHEN** GET /api/v2/prompts/chat/nonexistent
- **THEN** response is 404

#### Scenario: Reload prompts cache
- **GIVEN** an admin user
- **WHEN** POST /api/v2/prompts/reload
- **THEN** prompt cache is cleared and reloaded from files
- **AND** response is 200

#### Scenario: User selects prompt
- **GIVEN** an authenticated user
- **WHEN** PUT /api/v2/user/preferences with {preferred_chat_prompt: "formal"}
- **THEN** their chat responses use the "formal" prompt

---

### Requirement: Model Registry
The system SHALL separate model class mapping from configuration.

#### Scenario: Get model class by ID
- **GIVEN** available_models includes {id: "openai/gpt-4o", class: "OpenAILLM"}
- **WHEN** ModelRegistry.get("OpenAILLM") is called
- **THEN** returns the OpenAILLM class

#### Scenario: Unknown model class
- **WHEN** ModelRegistry.get("UnknownLLM") is called
- **THEN** raises KeyError

---

## Database Schema

### Dynamic Config Updates
```sql
ALTER TABLE dynamic_config ADD COLUMN IF NOT EXISTS
    active_condense_prompt VARCHAR(100) DEFAULT 'default',
    active_chat_prompt VARCHAR(100) DEFAULT 'default',
    active_system_prompt VARCHAR(100) DEFAULT 'default',
    top_p NUMERIC(3,2) DEFAULT 0.9,
    top_k INTEGER DEFAULT 50,
    repetition_penalty NUMERIC(4,2) DEFAULT 1.0,
    ingestion_schedule VARCHAR(100) DEFAULT '',
    verbosity INTEGER DEFAULT 3;
```

### Static Config Updates
```sql
ALTER TABLE static_config ADD COLUMN IF NOT EXISTS
    prompts_path TEXT DEFAULT '/root/A2rchi/prompts/';
```

### User Preferences Updates
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS
    preferred_condense_prompt VARCHAR(100),
    preferred_chat_prompt VARCHAR(100),
    preferred_system_prompt VARCHAR(100),
    preferred_max_tokens INTEGER,
    preferred_num_documents INTEGER,
    preferred_top_p NUMERIC(3,2),
    preferred_top_k INTEGER;
```

### Config Audit Table
```sql
CREATE TABLE IF NOT EXISTS config_audit (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(200) NOT NULL REFERENCES users(id),
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    config_type VARCHAR(20) NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT
);

CREATE INDEX IF NOT EXISTS idx_config_audit_user ON config_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_config_audit_time ON config_audit(changed_at);
```

---

## Contracts

### ConfigService

```python
class ConfigService:
    def __init__(self, pg_config: Dict[str, Any]):
        """Initialize with PostgreSQL config. Required."""
    
    def get_static_config(self) -> StaticConfig:
        """Get static configuration (cached after first load)."""
    
    def get_dynamic_config(self) -> DynamicConfig:
        """Get deployment-wide dynamic configuration."""
    
    def update_dynamic_config(
        self, 
        updates: Dict[str, Any], 
        user_id: str
    ) -> DynamicConfig:
        """
        Update dynamic config. Admin only (caller must verify).
        Logs to config_audit.
        """
    
    def get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get user's preferences."""
    
    def update_user_preferences(
        self, 
        user_id: str, 
        updates: Dict[str, Any]
    ) -> UserPreferences:
        """Update user's preferences."""
    
    def get_effective(self, field: str, user_id: str) -> Any:
        """
        Get effective value for field with precedence:
        user_pref > dynamic > static
        """
    
    def initialize_from_yaml(self, yaml_config: Dict) -> None:
        """
        Initialize/sync static_config from YAML.
        Called during a2rchi start.
        """
```

### PromptService

```python
class PromptService:
    def __init__(self, prompts_path: str):
        """Initialize with path to prompts directory."""
    
    def list_prompts(self) -> Dict[str, List[str]]:
        """List available prompts by type."""
    
    def get_prompt(self, prompt_type: str, name: str) -> str:
        """
        Get prompt content.
        Raises: FileNotFoundError if not found.
        """
    
    def reload(self) -> None:
        """Clear cache and reload from files."""
```

### ModelRegistry

```python
class ModelRegistry:
    @classmethod
    def get(cls, class_name: str) -> Type:
        """Get model class by name."""
    
    @classmethod
    def register(cls, class_name: str, model_class: Type) -> None:
        """Register a model class."""
    
    @classmethod
    def list_models(cls) -> List[str]:
        """List registered model class names."""
```

---

## File Deletions

The following files will be **removed**:
- `src/utils/config_loader.py` - Replaced by ConfigService
