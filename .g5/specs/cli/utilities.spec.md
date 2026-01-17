---
id: cli-utilities
title: CLI Utilities
version: 1.0.0
status: extracted
sources:
  - src/cli/utils/command_runner.py
  - src/cli/utils/helpers.py
  - src/cli/utils/grafana_styling.py
---

# CLI Utilities

Utility functions and classes for CLI operations.

## CommandRunner

Centralized command execution utility for Docker/Podman operations.

```python
class CommandRunner:
    """Centralized command execution utility"""
```

### Static Methods

#### `run_simple(command_str: str, cwd: Path = None) -> Tuple[str, str, int]`
Simple command execution without streaming.

**Contract:**
- POST: Returns (stdout, stderr, exit_code)
- POST: Command executed in specified `cwd`

#### `run_streaming(command_str: str, cwd: Path = None) -> Tuple[str, str, int]`
Run command with real-time output streaming.

**Contract:**
- POST: Returns (stdout, stderr, exit_code)
- POST: Output streamed to logger in real-time
- POST: Handles `KeyboardInterrupt` gracefully (terminates process)
- POST: Uses threading for non-blocking stream reads

---

## Helper Functions

Located in `src/cli/utils/helpers.py`.

### Docker/Podman Detection

#### `check_docker_available() -> bool`
Check if Docker is available and not just Podman emulation.

**Contract:**
- POST: Returns `True` if `docker` command exists and isn't podman emulation
- POST: Returns `False` if docker missing or is podman

### Option Parsers

Used as Click option callbacks.

#### `parse_gpu_ids_option(ctx, param, value) -> Optional[Union[str, List[int]]]`
Parse GPU IDs option.

**Contract:**
- POST: Returns `None` if value is None
- POST: Returns `"all"` if value is "all" (case-insensitive)
- POST: Returns list of integers for comma-separated IDs
- RAISES: `click.BadParameter` if invalid format

#### `parse_services_option(ctx, param, value) -> List[str]`
Parse comma-separated services list.

**Contract:**
- POST: Returns empty list if value is empty
- POST: Returns list of validated service names
- RAISES: `click.BadParameter` if invalid service name

#### `parse_sources_option(ctx, param, value) -> List[str]`
Parse comma-separated data sources list.

**Contract:**
- POST: Returns empty list if value is empty
- POST: Returns list of validated source names (excludes 'links')
- RAISES: `click.BadParameter` if invalid source name

### Validation

#### `validate_services_selection(services: List[str]) -> None`
Validate that at least one service is selected.

**Contract:**
- RAISES: `click.ClickException` if services list is empty
- RAISES: Exception includes list of available services

### Logging Helpers

#### `log_deployment_start(name: str, services: List[str], sources: List[str], dry: bool) -> None`
Log deployment start information.

#### `log_dependency_resolution(services: List[str], enabled_services: List[str]) -> None`
Log which dependencies were auto-enabled.

**Contract:**
- POST: Logs only if resolved services differ from requested

### Deployment Helpers

#### `handle_existing_deployment(base_dir: Path, name: str, force: bool, dry: bool, use_podman: bool) -> None`
Handle existing deployment - either remove it or raise error.

**Contract:**
- PRE: `base_dir` may or may not exist
- POST: If exists and `force`, deployment deleted
- POST: If exists and not `force`, raises `click.ClickException`
- POST: If not exists, no action taken

#### `print_dry_run_summary(name: str, services: List[str], resolved_services: List[str], sources: List[str], secrets: Set[str], plan: DeploymentPlan, flags: Dict, base_dir: Path) -> None`
Print summary of what would be created in a dry run.

---

## Grafana Styling

Located in `src/cli/utils/grafana_styling.py`.

#### `assign_feedback_palette(configs: List[Dict]) -> List[Dict]`
Produce a color palette for like/dislike feedback grouped by config name.

**Contract:**
- POST: Returns list of palette dicts, one per config
- POST: Each dict has `name`, `like` (green), `dislike` (red) colors
- POST: Colors cycle through predefined LIKE_COLORS and DISLIKE_COLORS

---

## Module: `_repository_info.py`

Git version information utilities.

#### `get_version() -> str`
Get the current git version tag.

**Contract:**
- POST: Returns version string from `git describe`
- POST: Returns "unknown" if not in git repository
