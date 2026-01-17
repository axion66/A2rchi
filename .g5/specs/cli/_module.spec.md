---
spec_id: cli
type: module
status: extracted
children:
  - cli/commands
  - cli/registries
  - cli/managers
  - cli/service-builder
  - cli/utilities
---

# CLI Module

Command-line interface for deploying and managing A2rchi services.

## Entry Point

```bash
a2rchi [COMMAND] [OPTIONS]
```

## Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize new deployment directory |
| `up` | Start services (docker-compose up) |
| `down` | Stop services |
| `build` | Build Docker images |
| `logs` | View service logs |
| `status` | Show running services |
| `config` | Manage configuration |

## Architecture

```
cli/
├── cli_main.py           # Click command definitions
├── service_registry.py   # Available services
├── source_registry.py    # Data source types
├── managers/
│   ├── docker_manager.py
│   ├── compose_manager.py
│   └── templates_manager.py
├── utils/
│   ├── command_runner.py
│   ├── helpers.py
│   ├── service_builder.py
│   └── grafana_styling.py
└── templates/
    ├── docker-compose.yaml.j2
    └── grafana/
```

## Service Registry

```python
SERVICES = {
    "chat": { "image": "a2rchi-chat", "ports": ["5000:5000"] },
    "grader": { "image": "a2rchi-grader", ... },
    "uploader": { "image": "a2rchi-uploader", ... },
    ...
}
```

## Source Registry

```python
SOURCES = {
    "links": { "collector": ScraperManager },
    "tickets": { "collector": TicketManager },
    ...
}
```

## Docker/Podman Support

Automatically detects container runtime:
- Prefers Docker if available
- Falls back to Podman
- Uses `docker-compose` or `podman-compose`
