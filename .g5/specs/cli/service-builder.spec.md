---
id: cli-service-builder
title: CLI Service Builder
version: 1.0.0
status: extracted
sources:
  - src/cli/utils/service_builder.py
---

# CLI Service Builder

Classes for building and configuring deployment plans.

## ServiceState

Holds compose-facing configuration for a single service.

```python
@dataclass
class ServiceState:
    enabled: bool = False
    image_name: str = ""
    tag: str = ""
    container_name: str = ""
    volume_name: str = ""
    required_secrets: List[str] = field(default_factory=list)
    required_config_fields: List[str] = field(default_factory=list)
    port_host: Optional[int] = None
    port_container: Optional[int] = None
```

### Methods

#### `to_dict() -> Dict[str, object]`
Convert state to dictionary for template rendering.

---

## DeploymentPlan

Immutable-ish view of the services, sources, and secrets for a deployment.

```python
class DeploymentPlan:
    def __init__(
        self,
        name: str,
        base_dir: Path,
        tag: str,
        use_podman: bool,
        gpu_ids: Optional[str],
        host_mode: bool,
        verbosity: int,
        benchmarking_dest: str,
    ):
        self.name = name
        self.base_dir = base_dir
        self.tag = tag
        self.use_podman = use_podman
        self.gpu_ids = gpu_ids
        self.host_mode = host_mode
        self.verbosity = verbosity
        self.benchmarking_dest = benchmarking_dest
        
        self.enabled_sources: Set[str] = set()
        self._required_secrets: Set[str] = set()
        self.services: Dict[str, ServiceState]  # Pre-initialized
        
        self.use_redmine: bool = False
        self.use_jira: bool = False
```

### Pre-initialized Services

The `services` dict is initialized with `ServiceState()` for:
- chromadb, postgres (infrastructure)
- chatbot, grafana, uploader, grader (application)
- piazza, mattermost, redmine-mailer (integration)
- benchmarking

### Methods

#### `enable_service(name: str, **config) -> None`
Enable a service with given configuration.

**Contract:**
- PRE: `name` is a known service
- POST: Service state set to enabled with config
- RAISES: `ValueError` if unknown service

#### `register_required_secrets(secrets: Set[str]) -> None`
Add secrets to required set.

#### `get_service(name: str) -> ServiceState`
Get service state by name.

**Contract:**
- RAISES: `ValueError` if unknown service

#### `get_enabled_services() -> List[str]`
Get list of enabled service names.

#### `get_required_volumes() -> List[str]`
Get sorted list of required volume names.

**Contract:**
- POST: Includes volumes from all enabled services
- POST: Includes `a2rchi-models` if `gpu_ids` is set

#### `get_required_secrets() -> List[str]`
Get sorted list of required secrets.

**Contract:**
- POST: Union of registered secrets and service secrets

#### `to_template_vars() -> Dict[str, object]`
Convert plan to dictionary for Jinja2 template rendering.

**Contract:**
- POST: Contains all plan attributes
- POST: Contains flattened service states with `{name}_enabled`, `{name}_image`, etc.

---

## ServiceBuilder

Static utility helpers for service and source enablement.

```python
class ServiceBuilder:
    @staticmethod
    def get_available_services() -> Dict[str, str]:
        """Get dict of service_name -> description"""
    
    @staticmethod
    def build_compose_config(
        name: str,
        verbosity: int,
        base_dir: Path,
        enabled_services: List[str],
        enabled_sources: List[str],
        secrets: Set[str],
        **flags
    ) -> DeploymentPlan:
        """Build complete deployment plan from inputs"""
```

### `build_compose_config`

Main factory method for creating deployment plans.

**Contract:**
- PRE: `name` is non-empty
- PRE: `enabled_services` contains valid service names
- POST: Returns fully configured `DeploymentPlan`
- POST: Dependencies resolved and auto-enabled
- POST: Secrets collected from services and sources
- POST: Volumes computed for enabled services

#### Process:
1. Create `DeploymentPlan` with base settings
2. Resolve service dependencies via registry
3. For each enabled service:
   - Get `ServiceDefinition` from registry
   - Compute image/container/volume names
   - Set port configuration
   - Track required secrets
4. Set source flags (`use_redmine`, `use_jira`)
5. Return configured plan

---

## Usage Example

```python
from src.cli.utils.service_builder import ServiceBuilder

# Get available services for --services option
available = ServiceBuilder.get_available_services()
# {'chatbot': 'Interactive chat interface...', 'grafana': '...', ...}

# Build deployment plan
plan = ServiceBuilder.build_compose_config(
    name="mybot",
    verbosity=3,
    base_dir=Path("~/.a2rchi/a2rchi-mybot"),
    enabled_services=["chatbot", "grafana"],
    enabled_sources=["links", "git"],
    secrets={"PG_PASSWORD", "OPENAI_API_KEY"},
    tag="2000",
    podman=False,
    gpu_ids=None,
    host_mode=False,
)

# Access plan for templates
vars = plan.to_template_vars()
```
