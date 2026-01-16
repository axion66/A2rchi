---
spec_id: utils/logging
type: module
source_files:
  - src/utils/logging.py
test_file: null
status: extracted
---

# Logging Utilities

> ⚠️ **AUTO-GENERATED FROM CODE**: Review for accuracy.

## Overview

Configures Python logging for A2rchi. Supports both config-driven setup (for services) and CLI-style setup with custom verbosity levels.

## Structured Design Doc

### Constants

#### `ignore_debug_modules`
- **Value**: `["urllib3.connectionpool", "filelock", "httpcore", "openai._base_client"]`
- **Purpose**: Modules to suppress at DEBUG level (too verbose)

#### `logging_verboseLevel`
- **Value**: `[CRITICAL, ERROR, WARNING, INFO, DEBUG]`
- **Purpose**: Maps verbosity 0-4 to Python logging levels

### Functions

#### `setup_logging() -> None`

Configure logging based on global config verbosity.

**Contracts:**
- PRE: Global config is loadable via `load_global_config()`
- PRE: Config has `verbosity` key (0-4)
- POST: Root logger configured with level from config
- POST: Werkzeug logger set to same level
- POST: If verbosity=4, noisy modules set to INFO instead of DEBUG

#### `setup_cli_logging(verbosity: int) -> None`

Configure logging for CLI mode.

**Contracts:**
- PRE: `verbosity` is int 0-4
- POST: If verbosity > 3, format: `[%(name)s] %(levelname)s: %(message)s`
- POST: If verbosity <= 3, format: `[A2RCHI] %(message)s`

#### `get_logger(name: str, verbosity: int = None) -> logging.Logger`

Get a named logger, optionally setting its verbosity.

**Contracts:**
- PRE: `name` is string
- POST: Returns `logging.Logger` instance
- POST: If `verbosity` provided, logger level set accordingly

## Guardrails

- Verbosity clamped to 0-4 range
- Uses `force=True` in basicConfig to override existing config

## Testing Contracts

- setup_logging sets correct level from config
- setup_cli_logging uses simple format at low verbosity
- get_logger returns named logger
