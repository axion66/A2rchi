---
spec_id: utils/config-loader
type: module
source_files:
  - src/utils/config_loader.py
test_file: null
status: extracted
---

# Config Loader

> ⚠️ **AUTO-GENERATED FROM CODE**: Review for accuracy.

## Overview

Loads YAML configuration files from `/root/A2rchi/configs/`. Provides functions to load full config or specific sections. Optionally maps model class strings to actual Python classes.

## Structured Design Doc

### Constants

#### `CONFIGS_PATH`
- **Value**: `/root/A2rchi/configs/`
- **Purpose**: Root directory for all config files

### Functions

#### `load_config(map: bool = False, name: str = None) -> dict`

Load complete configuration, optionally mapping model classes.

**Contracts:**
- PRE: If `name` provided, `{CONFIGS_PATH}{name}.yaml` must exist
- PRE: If `name` is None, at least one `.yaml` file must exist in `CONFIGS_PATH`
- POST: Returns dict with full config structure
- POST: If `map=True`, `config["a2rchi"]["model_class_map"][*]["class"]` are actual class objects
- POST: If `map=True`, `config["data_manager"]["embedding_class_map"][*]["class"]` are actual class objects
- ERROR: `FileNotFoundError` if config file not found
- ERROR: `yaml.YAMLError` if invalid YAML

#### `load_global_config(name: str = None) -> dict`

Load only the `global` section of config.

**Contracts:**
- PRE: Same as `load_config`
- POST: Returns `config["global"]`

#### `load_utils_config(name: str = None) -> dict`

Load only the `utils` section of config.

**Contracts:**
- PRE: Same as `load_config`
- POST: Returns `config.get("utils", {}) or {}`

#### `load_data_manager_config(name: str = None) -> dict`

Load only the `data_manager` section of config.

**Contracts:**
- PRE: Same as `load_config`
- POST: Returns `config["data_manager"]`

#### `load_services_config(name: str = None) -> dict`

Load only the `services` section of config.

**Contracts:**
- PRE: Same as `load_config`
- POST: Returns `config["services"]`

#### `get_config_names() -> list[str]`

List available configuration names.

**Contracts:**
- PRE: `CONFIGS_PATH` directory exists
- POST: Returns list of config names (without `.yaml` extension)

## Guardrails

- Config path is hardcoded - deployment must mount configs at `/root/A2rchi/configs/`
- Uses `yaml.FullLoader` - config files are trusted

## Testing Contracts

- Load config by name returns correct structure
- Load config with map=True replaces class strings with classes
- Missing config raises FileNotFoundError
- Section loaders return correct subsections
