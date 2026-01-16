---
name: g5-documentation
description: Guide for generating documentation from specs. Use when creating READMEs, API documentation, or any docs that should derive from specs.
---

# G5 Documentation

This skill guides you through generating documentation from specs.

## When to Use This Skill

- Creating or updating README files
- Generating API documentation
- Writing user guides from specs
- Keeping docs in sync with code

## Documentation Philosophy

In G5, **specs are the source of truth**. Documentation should derive from specs, not the other way around.

```
Spec (source) → Documentation (derived)
              → Code (derived)
              → Tests (derived)
```

## Spec-to-Doc Mapping

| Spec Section | Documentation Type |
|--------------|-------------------|
| Overview | README introduction |
| Structured Design Doc | API reference |
| Contracts | Usage examples |
| Testing Contracts | Test documentation |
| Guardrails | Constraints/limitations |

## README Generation

### From Spec Overview

```markdown
# Spec: specs/auth/service.spec.md
## Overview
AuthService handles user authentication including login,
logout, and token management. It supports JWT tokens
with configurable expiration.

# Generated: README.md
## Authentication Service

AuthService handles user authentication including login,
logout, and token management. It supports JWT tokens
with configurable expiration.
```

### From Structured Design Doc

```markdown
# Spec: Structured Design Doc
##### `login(username: str, password: str) -> Token`
Authenticate user and return JWT token.

# Generated: API Reference
### `login(username, password)`

Authenticate user and return JWT token.

**Parameters:**
- `username` (str): User's username
- `password` (str): User's password

**Returns:**
- `Token`: JWT token object
```

### From Contracts

```markdown
# Spec: Contracts
- PRE: username is not empty
- PRE: password meets minimum length
- POST: returns valid JWT token
- ERROR: AuthenticationError when credentials invalid

# Generated: Usage Examples
```python
# Basic usage
token = auth.login("user@example.com", "password123")

# Error handling
try:
    token = auth.login("user", "short")
except AuthenticationError:
    print("Invalid credentials")
```
```

## Documentation Templates

### README.md

```markdown
# {Project Name}

{From spec overview}

## Installation

{Installation instructions}

## Quick Start

{From spec examples/contracts}

## API Reference

{From Structured Design Doc}

### {ClassName}

{Class description from spec}

#### `method_name(params)`

{Method description}

**Parameters:**
{From spec signature}

**Returns:**
{From spec signature}

**Raises:**
{From spec ERROR conditions}

## Configuration

{From spec guardrails/constants}

## Contributing

{Standard contributing guide}
```

### API Reference

```markdown
# API Reference

## Classes

### {ClassName}

{From spec overview}

#### Constructor

```python
{constructor signature from spec}
```

#### Methods

##### `method_name(param1: Type1, param2: Type2) -> ReturnType`

{Description from spec}

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| param1 | Type1 | {from spec} |
| param2 | Type2 | {from spec} |

**Returns:**

{ReturnType}: {description from POST condition}

**Raises:**

- `ErrorType`: {from ERROR condition}

**Example:**

```python
{derived from contracts}
```
```

## Doc Generation Workflow

### Manual Approach

1. Read spec's Structured Design Doc
2. Transform to documentation format
3. Add examples from contracts
4. Include error handling from ERROR conditions

### Semi-Automated

```python
# Example doc generator script
def generate_api_doc(spec_path: str) -> str:
    spec = parse_spec(spec_path)
    doc = []
    
    # Overview → Introduction
    doc.append(f"# {spec.component_id}\n")
    doc.append(spec.overview)
    
    # Classes → API Reference
    for cls in spec.classes:
        doc.append(f"\n## {cls.name}\n")
        for method in cls.methods:
            doc.append(format_method(method))
    
    return "\n".join(doc)
```

## Keeping Docs in Sync

### Option 1: Docs as Views

Use the views system to create auto-syncing docs:

```yaml
# .g5/views/specs/api-docs.view-spec.md
type: view-spec
name: API Documentation

sections:
  - name: "Introduction"
    source: "specs/auth.spec.md#Overview"
    lock: readonly
    
  - name: "API Reference"
    source: "specs/auth.spec.md#Structured Design Doc"
    lock: readonly
```

### Option 2: Doc Update Workflow

Create a workflow specifically for doc updates:

1. Spec changes trigger doc workflow
2. Regenerate docs from specs
3. Review and commit

### Option 3: CI Check

```yaml
# .github/workflows/docs.yml
- name: Check docs in sync
  run: |
    python scripts/generate_docs.py
    git diff --exit-code docs/
```

## Common Documentation Patterns

### Usage Examples

Derive from contracts:

```markdown
# From spec:
- PRE: data is valid JSON string
- POST: returns parsed dictionary
- ERROR: JSONDecodeError on invalid JSON

# Generate:
## Examples

### Basic Usage
```python
result = parser.parse('{"key": "value"}')
print(result)  # {'key': 'value'}
```

### Error Handling
```python
try:
    result = parser.parse('invalid json')
except JSONDecodeError as e:
    print(f"Invalid JSON: {e}")
```
```

### Configuration Reference

Derive from constants and guardrails:

```markdown
# From spec:
### Constants
- MAX_CONNECTIONS = 100
- TIMEOUT_SECONDS = 30

## Guardrails
- Connection count must not exceed MAX_CONNECTIONS

# Generate:
## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| max_connections | 100 | Maximum concurrent connections |
| timeout | 30s | Request timeout |

**Note:** Connection count must not exceed max_connections.
```

## Common Mistakes

1. **Docs diverge from specs** - Always regenerate from specs
2. **Manual-only docs** - Automate where possible
3. **Missing error handling docs** - Include all ERROR conditions
4. **No examples** - Derive examples from contracts
5. **Outdated installation** - Keep install instructions current

## Documentation Checklist

- [ ] README has overview from spec
- [ ] API reference matches Structured Design Doc
- [ ] All public methods documented
- [ ] Error conditions included
- [ ] Examples derived from contracts
- [ ] Configuration options documented
- [ ] Sync mechanism in place

> 💡 **Related skills**: 
> - [g5-spec-writing](../g5-spec-writing/SKILL.md) for source specs
> - [g5-viewgen](../g5-viewgen/SKILL.md) for auto-syncing docs
