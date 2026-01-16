---
spec_id: utils/env
type: module
source_files:
  - src/utils/env.py
test_file: null
status: extracted
---

# Environment Utilities

> ⚠️ **AUTO-GENERATED FROM CODE**: Review for accuracy.

## Overview

Utility for reading Docker-style secrets from files. Follows the convention where `{SECRET_NAME}_FILE` environment variable points to a file containing the secret value.

## Structured Design Doc

### Functions

#### `read_secret(secret_name: str) -> str`

Read a secret value from a file path stored in environment variable.

**Contracts:**
- PRE: `secret_name` is a string
- POST: If env var `{secret_name}_FILE` exists and points to valid file, returns file contents (stripped)
- POST: If env var `{secret_name}_FILE` does not exist, returns empty string
- POST: Return value has leading/trailing whitespace stripped
- ERROR: `FileNotFoundError` if env var set but file doesn't exist

## Guardrails

- Returns empty string (not None) when env var missing
- Strips whitespace from secret value

## Testing Contracts

- Read secret with valid env var and file returns contents
- Read secret with missing env var returns empty string
- Read secret strips whitespace from file contents
