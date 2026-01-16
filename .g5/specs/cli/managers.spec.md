---
id: cli-managers
title: CLI Managers
version: 1.0.0
status: extracted
sources:
  - src/cli/managers/config_manager.py
  - src/cli/managers/deployment_manager.py
  - src/cli/managers/secrets_manager.py
  - src/cli/managers/templates_manager.py
  - src/cli/managers/volume_manager.py
---

# CLI Managers

Manager classes for configuration, deployment, secrets, templates, and volumes.

## ConfigurationManager

Manages A2rchi configuration loading, merging, and validation.

```python
class ConfigurationManager:
    def __init__(self, config_paths_list: List[str], env: Environment):
        self.configs: List[Dict[str, Any]] = []
        self.config: Dict[str, Any]  # First config (primary)
        self.env: Environment  # Jinja2 environment
```

### Methods

#### `validate_configs(services: List[str], sources: Optional[List[str]] = None) -> None`
Validate all required fields are present in each config.

**Contract:**
- PRE: At least one config loaded
- POST: All service-specific fields present
- POST: All source-specific fields present
- POST: All pipeline requirements satisfied
- RAISES: `ValueError` if missing required field

#### `get_enabled_sources() -> List[str]`
Get sources enabled in config.

#### `get_disabled_sources() -> List[str]`
Get sources explicitly disabled in config.

#### `set_sources_enabled(sources: List[str]) -> None`
Update config with enabled sources list.

#### `get_configs() -> List[Dict[str, Any]]`
Get all loaded configurations.

#### `get_models_configs() -> List[Dict]`
Get model configurations from all configs.

### Private Methods

#### `_load_config(config_filepath: Path) -> Dict[str, Any]`
Load and validate basic structure of config file.

**Contract:**
- RAISES: `FileNotFoundError` if file not found
- RAISES: `ValueError` if file is empty or invalid YAML

#### `_append(config: Dict) -> None`
Append config if static portions match previous configs.

**Contract:**
- PRE: Static fields (global, services) must be consistent across all configs
- RAISES: `ValueError` if static fields mismatch

---

## DeploymentManager

Manages container deployment using Docker/Podman Compose.

```python
class DeploymentError(Exception):
    """Custom exception for deployment failures"""
    def __init__(self, message: str, exit_code: int, stderr: str = None):
        self.exit_code = exit_code
        self.stderr = stderr

class DeploymentManager:
    def __init__(self, use_podman: bool = False):
        self.use_podman = use_podman
        self.compose_tool = "podman compose" if use_podman else "docker compose"
```

### Methods

#### `start_deployment(deployment_dir: Path) -> None`
Start the deployment using compose.

**Contract:**
- PRE: `compose.yaml` exists in deployment_dir
- POST: All containers started successfully
- RAISES: `FileNotFoundError` if compose file missing
- RAISES: `DeploymentError` if compose up fails

#### `stop_deployment(deployment_dir: Path) -> None`
Stop the deployment.

**Contract:**
- PRE: `compose.yaml` exists in deployment_dir
- POST: All containers stopped
- RAISES: `FileNotFoundError` if compose file missing

#### `delete_deployment(deployment_name: str, remove_images: bool = False, remove_volumes: bool = False, remove_files: bool = True) -> None`
Delete a deployment and optionally clean up resources.

**Contract:**
- POST: Deployment stopped
- POST: If `remove_images`, associated images removed
- POST: If `remove_volumes`, associated volumes removed
- POST: If `remove_files`, deployment directory removed

---

## SecretsManager

Manages secret loading and validation using .env files.

```python
class SecretsManager:
    def __init__(self, env_file_path: str = None, config_manager = None):
        self.env_file_path: Path
        self.secrets: Dict[str, str]
        self.config_manager: ConfigurationManager
```

### Methods

#### `get_secrets(services: Set[str], sources: Set[str]) -> Tuple[Set[str], Set[str]]`
Return (required_secrets, all_secrets) for services and sources.

**Contract:**
- POST: First set is required secrets based on config
- POST: Second set is all secrets found in .env file

#### `get_required_secrets_for_services(services: Set[str]) -> Set[str]`
Determine required secrets based on enabled services.

**Contract:**
- POST: Always includes `PG_PASSWORD`
- POST: Includes model-based secrets (OPENAI_API_KEY, ANTHROPIC_API_KEY)
- POST: Includes embedding secrets
- POST: Includes registry-defined service secrets

#### `get_required_secrets_for_sources(sources: Set[str]) -> Set[str]`
Get required secrets for data sources.

#### `validate_secrets(required_secrets: Set[str]) -> None`
Validate that all required secrets are available.

**Contract:**
- POST: All required secrets have non-empty values
- RAISES: `ValueError` with list of missing secrets

#### `get_secret(key: str) -> str`
Get a secret value by exact key match.

**Contract:**
- RAISES: `KeyError` if secret not found

#### `write_secrets_to_files(target_dir: Path, secrets: Set[str]) -> None`
Write secrets to individual files in secrets/ subdirectory.

**Contract:**
- POST: Creates `{target_dir}/secrets/` directory
- POST: Each secret written to `{name.lower()}.txt`

---

## TemplateManager

Manages Jinja2 template rendering and file preparation.

```python
@dataclass
class TemplateContext:
    plan: DeploymentPlan
    config_manager: ConfigurationManager
    secrets_manager: SecretsManager
    options: Dict[str, Any]
    base_dir: Path  # Set in __post_init__
    prompt_mappings: Dict[str, Dict[str, str]]

class TemplateManager:
    def __init__(self, jinja_env: Environment):
        self.env = jinja_env
        self.registry = service_registry
```

### Methods

#### `prepare_deployment_files(plan: DeploymentPlan, config_manager, secrets_manager, **options) -> None`
Prepare all deployment artifacts.

**Contract:**
- POST: Prompts copied to deployment directory
- POST: Config files rendered
- POST: Service-specific artifacts created (grafana, grader)
- POST: PostgreSQL init.sql created
- POST: compose.yaml rendered
- POST: Web lists copied if present

### Template Files

- `base-config.yaml` - A2rchi configuration template
- `base-compose.yaml` - Docker Compose template
- `base-init.sql` - PostgreSQL initialization
- `grafana/` - Grafana dashboard templates

---

## VolumeManager

Manages Docker/Podman volume creation and removal.

```python
class VolumeManager:
    def __init__(self, use_podman: bool = False):
        self.use_podman = use_podman
        self.container_tool = "podman" if use_podman else "docker"
```

### Methods

#### `create_required_volumes(compose_config: DeploymentPlan) -> None`
Create all volumes required by the deployment.

**Contract:**
- POST: All volumes from `compose_config.get_required_volumes()` exist
- POST: Existing volumes are not recreated

#### `remove_volume(volume_name_substr: str, force: bool = False) -> None`
Remove any volume ending with `-{volume_name_substr}`.

**Contract:**
- POST: All matching volumes removed (or warning logged)

#### `remove_deployment_volumes(deployment_name: str, force: bool = False) -> None`
Remove all volumes for a deployment.

### Private Methods

#### `_create_volume(volume_name: str) -> None`
Create a single volume if it doesn't exist.

**Contract:**
- POST: Volume exists
- RAISES: `RuntimeError` if creation fails

#### `_volume_exists(volume_name: str) -> bool`
Check if a volume already exists.
