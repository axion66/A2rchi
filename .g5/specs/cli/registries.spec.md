---
id: cli-registries
title: CLI Registries
version: 1.0.0
status: extracted
sources:
  - src/cli/service_registry.py
  - src/cli/source_registry.py
---

# CLI Registries

Central registries for available services and data sources in the A2rchi CLI.

## ServiceDefinition

Dataclass defining a service's complete configuration.

```python
@dataclass
class ServiceDefinition:
    """Complete definition of a service"""
    name: str
    description: str
    category: str  # 'infrastructure', 'application', 'integration'
    
    # Service configuration
    requires_image: bool = True
    requires_volume: bool = False
    auto_enable: bool = False
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    requires_services: List[str] = field(default_factory=list)
    
    # Secrets and config
    required_secrets: List[str] = field(default_factory=list)
    required_config_fields: List[str] = field(default_factory=list)
    
    # Port configuration
    default_host_port: Optional[int] = None
    default_container_port: Optional[int] = None
    port_config_path: Optional[str] = None
    
    # Volume naming strategy
    volume_name_pattern: Optional[str] = None
```

### Methods

#### `get_volume_name(deployment_name: str) -> Optional[str]`
Generate volume name for this service.

**Contract:**
- PRE: `deployment_name` is non-empty string
- POST: Returns formatted volume name if `requires_volume`, else None
- POST: Uses `volume_name_pattern` if set, else default `a2rchi-{name}`

#### `get_image_name(deployment_name: str) -> Optional[str]`
Generate image name for this service.

**Contract:**
- POST: Returns `{service_name}-{deployment_name}` if `requires_image`, else None

#### `get_container_name(deployment_name: str) -> str`
Generate container name for this service.

**Contract:**
- POST: Returns `{service_name}-{deployment_name}`

---

## ServiceRegistry

Central registry of all available services.

```python
class ServiceRegistry:
    def __init__(self):
        self._services: Dict[str, ServiceDefinition] = {}
        self._register_default_services()
```

### Methods

#### `register(service: ServiceDefinition) -> None`
Register a new service definition.

**Contract:**
- PRE: `service.name` not already registered
- POST: Service is retrievable via `get()`
- RAISES: `ValueError` if name already exists

#### `get(name: str) -> ServiceDefinition`
Get a service by name.

**Contract:**
- RAISES: `KeyError` if service not found

#### `resolve_dependencies(services: List[str]) -> List[str]`
Return services including their dependency closure.

**Contract:**
- POST: Returns topologically sorted list
- POST: All dependencies of input services are included
- POST: Infrastructure services auto-added based on `auto_enable`
- INV: No duplicate entries in result

#### `get_all_services() -> List[str]`
Get all registered service names.

#### `get_application_services() -> Dict[str, ServiceDefinition]`
Get services with category 'application'.

#### `get_integration_services() -> Dict[str, ServiceDefinition]`
Get services with category 'integration'.

#### `get_required_secrets(services: List[str]) -> Set[str]`
Collect required secrets for given services.

**Contract:**
- POST: Union of `required_secrets` for all services in list

### Default Services

Infrastructure (auto-enabled):
- `chromadb` - Vector database
- `postgres` - PostgreSQL database

Application:
- `chatbot` - Chat interface
- `grafana` - Monitoring dashboard
- `uploader` - Document upload service
- `grader` - Assignment grading service

Integration:
- `piazza` - Piazza forum integration
- `mattermost` - Mattermost chat integration
- `redmine-mailer` - Redmine ticket integration

---

## SourceDefinition

Dataclass for data ingestion source metadata.

```python
@dataclass
class SourceDefinition:
    name: str
    description: str
    required_secrets: List[str] = field(default_factory=list)
    required_config_fields: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
```

---

## SourceRegistry

Registry of supported data sources.

```python
class SourceRegistry:
    def __init__(self):
        self._sources: Dict[str, SourceDefinition] = {}
        self._register_defaults()
```

### Methods

#### `register(source_def: SourceDefinition) -> None`
Register a new source definition.

#### `resolve_dependencies(sources: List[str]) -> List[str]`
Return sources including their dependency closure.

**Contract:**
- POST: Topologically sorted with dependencies first
- POST: Unknown sources are silently skipped

#### `names() -> List[str]`
Get all registered source names.

#### `required_secrets(sources: List[str]) -> List[str]`
Collect required secrets for given sources.

#### `required_config_fields(sources: List[str]) -> List[str]`
Collect required config fields for given sources.

### Default Sources

- `links` - Basic HTTP/HTTPS link scraping (no secrets)
- `sso` - SSO-backed web crawling (SSO_USERNAME, SSO_PASSWORD)
- `git` - Git repository scraping (GIT_USERNAME, GIT_TOKEN)
- `jira` - Jira integration (JIRA_PAT)
- `redmine` - Redmine tickets (REDMINE_USER, REDMINE_PW)

---

## Module Globals

```python
# Singleton instances
service_registry = ServiceRegistry()
source_registry = SourceRegistry()
```

These are instantiated at module load and used throughout the CLI.
