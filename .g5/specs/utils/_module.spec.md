---
spec_id: utils
type: module
status: extracted
children:
  - utils/config-loader
  - utils/env
  - utils/logging
  - utils/sql
  - utils/benchmark-report
---

# Utils Module

Shared utilities used across all A2rchi modules.

## Exports

```python
from src.utils.config_loader import load_config
from src.utils.env import read_secret
from src.utils.logging import get_logger
from src.utils import sql
```

## Components

### config_loader

```python
def load_config(map: bool = False, name: str = None) -> Dict
```

Loads YAML configuration with:
- Environment variable substitution (`${VAR}`)
- Optional model class mapping (`map=True`)
- Named config support (`name="production"`)

### env

```python
def read_secret(secret_name: str) -> str
```

Reads secrets from Docker secrets or environment variables.

### logging

```python
def get_logger(name: str) -> Logger
```

Centralized logging with consistent format across modules.

### sql

SQL query constants for PostgreSQL operations:
- `INSERT_TIMING`, `INSERT_HISTORY`, `INSERT_FEEDBACK`
- `SELECT_CONVERSATIONS`, `SELECT_MESSAGES`
- etc.

### benchmark_report

CLI tool to generate HTML reports from benchmark results.

## Usage Pattern

All modules should:

```python
from src.utils.logging import get_logger
from src.utils.config_loader import load_config

logger = get_logger(__name__)
config = load_config()
```
