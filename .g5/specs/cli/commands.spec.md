---
id: cli-commands
title: CLI Commands
version: 1.0.0
status: extracted
sources:
  - src/cli/cli_main.py
---

# CLI Commands

Click-based command-line interface for A2rchi deployment management.

## Entry Point

```python
@click.group()
def cli():
    pass

def main():
    """Entrypoint for a2rchi cli tool"""
    cli.add_command(create)
    cli.add_command(delete)
    cli.add_command(list_services)
    cli.add_command(list_deployments)
    cli.add_command(evaluate)
    cli()
```

---

## `create` Command

Create an A2RCHI deployment with selected services and data sources.

```bash
a2rchi create --name mybot --config config.yaml --services chatbot,grafana
```

### Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--name, -n` | str | Yes | Name of the deployment |
| `--config, -c` | str | No* | Path to .yaml configuration |
| `--config-dir, -cd` | str | No* | Path to configs directory |
| `--env-file, -e` | str | No | Path to .env file with secrets |
| `--services, -s` | str | No | Comma-separated list of services |
| `--sources, -src` | str | No | Comma-separated list of data sources |
| `--podman, -p` | flag | No | Use Podman instead of Docker |
| `--gpu-ids` | str | No | GPU config: "all" or comma-separated IDs |
| `--tag, -t` | str | No | Image tag (default: "2000") |
| `--hostmode` | flag | No | Use host network mode |
| `--verbosity, -v` | int | No | Logging level 0-4 (default: 3) |
| `--force, -f` | flag | No | Overwrite existing deployment |
| `--dry, --dry-run` | flag | No | Show what would be created |

*Must specify exactly one of `--config` or `--config-dir`

### Contract

**Preconditions:**
- Either `--config` or `--config-dir` specified (not both)
- At least one service specified
- Docker available (unless `--podman`)

**Postconditions:**
- Deployment directory created at `~/.a2rchi/a2rchi-{name}/`
- Config files rendered
- Secrets written to files
- Volumes created
- Containers started

**Raises:**
- `ClickException` if validation fails
- `ClickException` if deployment exists and no `--force`

### Process Flow

1. Parse and validate options
2. Load configurations via `ConfigurationManager`
3. Load secrets via `SecretsManager`
4. Reconcile sources (CLI + config enabled - config disabled)
5. Validate configs and secrets
6. Build `DeploymentPlan` via `ServiceBuilder`
7. If dry run: print summary and exit
8. Create deployment directory
9. Write secrets to files
10. Create volumes via `VolumeManager`
11. Render templates via `TemplateManager`
12. Start deployment via `DeploymentManager`

---

## `delete` Command

Delete an A2RCHI deployment.

```bash
a2rchi delete --name mybot --rmi --rmv
```

### Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--name, -n` | str | No* | Name of deployment to delete |
| `--list` | flag | No | List all available deployments |
| `--rmi` | flag | No | Remove images |
| `--rmv` | flag | No | Remove volumes (prompts for confirmation) |
| `--keep-files` | flag | No | Keep deployment files |
| `--verbosity, -v` | int | No | Logging level 0-4 (default: 3) |
| `--podman, -p` | flag | No | Use Podman |

*Required unless `--list` specified

### Contract

**Postconditions:**
- Containers stopped
- If `--rmi`: images removed
- If `--rmv`: volumes removed (after confirmation)
- Unless `--keep-files`: deployment directory removed

---

## `list_services` Command

List all available services and data sources.

```bash
a2rchi list-services
```

### Output Format

```
Available A2RCHI services:

Application Services:
  chatbot              Interactive chat interface...
  grafana              Monitoring dashboard...

Integration Services:
  piazza               Piazza forum integration...

Data Sources:
  git                  Git repository scraping...
  sso                  SSO-backed web crawling...
```

---

## `list_deployments` Command

List all existing deployments.

```bash
a2rchi list-deployments
```

### Contract

**Postconditions:**
- Lists directories in `~/.a2rchi/` matching `a2rchi-*`
- Shows status (complete, incomplete, unknown)

---

## `evaluate` Command

Create a benchmarking deployment for performance evaluation.

```bash
a2rchi evaluate --name bench1 --config config.yaml --sources git
```

### Options

Similar to `create` but:
- No `--services` option (uses fixed set: chromadb, postgres, benchmarking)
- Reads benchmarking config for query file and output directory

### Contract

**Preconditions:**
- Configuration contains `benchmarking` interface config

**Postconditions:**
- Benchmarking deployment created
- Query file and output directory configured

---

## Global Constants

```python
A2RCHI_DIR = os.environ.get('A2RCHI_DIR', os.path.join(os.path.expanduser('~'), ".a2rchi"))
```

Environment variable to override default deployment location.

---

## Jinja2 Environment

```python
env = Environment(
    loader=PackageLoader("src.cli"),
    autoescape=select_autoescape(),
    undefined=ChainableUndefined,
)
```

Templates loaded from `src/cli/templates/` package.
