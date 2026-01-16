# Design Doc: Uplift CLI Module

## Overview
Extract G5 specs from the `src/cli/` module - the command-line interface for creating and managing A2rchi deployments.

## Goals
- Document CLI entry points and commands
- Spec the manager classes (config, deployment, secrets, templates, volume)
- Spec the registry pattern (service and source registries)
- Spec utility functions (command runner, helpers, service builder)

## Non-Goals
- Changing any existing functionality
- Adding new CLI commands

## Module Structure

```
src/cli/
├── __init__.py
├── cli_main.py              # Click commands (create, delete, list, etc.)
├── service_registry.py      # ServiceDefinition, ServiceRegistry
├── source_registry.py       # SourceDefinition, SourceRegistry
├── managers/
│   ├── config_manager.py    # ConfigurationManager
│   ├── deployment_manager.py # DeploymentManager, DeploymentError
│   ├── secrets_manager.py   # SecretsManager
│   ├── templates_manager.py # TemplateManager, TemplateContext
│   └── volume_manager.py    # VolumeManager
├── utils/
│   ├── command_runner.py    # CommandRunner
│   ├── helpers.py           # CLI helper functions
│   ├── service_builder.py   # ServiceState, DeploymentPlan, ServiceBuilder
│   ├── grafana_styling.py   # Grafana dashboard styling
│   └── _repository_info.py  # Git version info
└── templates/               # Jinja2 templates (not code)
```

## Spec Plan

### 1. Registries (`cli/registries.spec.md`)
- `ServiceDefinition` - dataclass for service metadata
- `ServiceRegistry` - central registry of available services
- `SourceDefinition` - dataclass for data source metadata  
- `SourceRegistry` - registry of data ingestion sources

### 2. Managers (`cli/managers.spec.md`)
- `ConfigurationManager` - config loading, validation, merging
- `DeploymentManager` - compose deployment lifecycle
- `SecretsManager` - .env file loading and validation
- `TemplateManager` - Jinja2 template rendering
- `VolumeManager` - Docker/Podman volume management

### 3. Service Builder (`cli/service-builder.spec.md`)
- `ServiceState` - compose-facing config for a service
- `DeploymentPlan` - immutable view of deployment config
- `ServiceBuilder` - utility for service enablement

### 4. Utilities (`cli/utilities.spec.md`)
- `CommandRunner` - centralized command execution
- Helper functions (parse options, validation, logging)

### 5. CLI Commands (`cli/commands.spec.md`)
- `create` command - main deployment creation
- `delete` command - deployment cleanup
- `list` command - list deployments

## Success Criteria
- All public classes and functions have specs
- Contracts document validation rules and error conditions
- Dependencies between components are clear
