# Uplift Utils Module

## Overview

Extract specs from `src/utils/` - the core utility modules used across A2rchi.

## Goals

1. Extract specs from existing code in `src/utils/`
2. Document contracts for config loading, logging, and SQL utilities
3. Enable spec-driven development for future changes to utils

## Non-Goals

- Refactoring existing code
- Adding new features
- Changing existing behavior

## Source Files

| File | Lines | Description |
|------|-------|-------------|
| `config_loader.py` | 148 | YAML config loading with model mapping |
| `env.py` | 15 | Secret/environment variable reading |
| `logging.py` | 56 | Logging setup and configuration |
| `sql.py` | 128 | SQL query constants |
| `generate_benchmark_report.py` | 479 | Benchmark HTML report generator |

## Affected Specs

specs:
  - .g5/specs/utils/config-loader.spec.md
  - .g5/specs/utils/env.spec.md
  - .g5/specs/utils/logging.spec.md
  - .g5/specs/utils/sql.spec.md
  - .g5/specs/utils/benchmark-report.spec.md

## Design Decisions

1. **Spec per file** - Each Python file gets one spec
2. **Constants documented** - SQL queries documented as module contracts
3. **Test gaps noted** - No existing unit tests for utils
