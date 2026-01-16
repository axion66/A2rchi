---
name: g5-viewgen
description: Guide for generating synchronized view instances from view specs. Use when creating views, working with the views system, understanding view specs, or managing view synchronization.
---

# G5 View Generation

This skill guides you through the views system and generating view instances.

## When to Use This Skill

- Creating new view instances
- Understanding view spec format
- Working with view synchronization
- Managing input context mapping
- Dealing with view conflicts

## Views System Overview

```
View Spec (template)          View Instance (generated)
.g5/views/specs/              .g5/views/
├── security-review.view-spec.md  ├── security-review--auth.view.md
├── pm-review.view-spec.md        ├── security-review--user.view.md
└── testing.view-spec.md          └── pm-review--auth.view.md
```

**Key Concepts:**
- **View Spec**: Template defining view structure, sections, sources
- **View Instance**: Generated file synchronized with sources
- **Input Context Mapping**: How to extract content from sources

## View Spec Format

```yaml
# .g5/views/specs/security-review.view-spec.md
---
type: view-spec
name: Security Review
persona: Security Engineer
generation: dynamic

triggers:
  - on: file_changed
    pattern: "specs/**/*.spec.md"

instances:
  pattern: "specs/**/*.spec.md"

sections:
  - name: "Interface"
    source: "${target}#Interface"
    lock: readonly
    conflict: source-wins
    
  - name: "Threat Model"
    lock: editable
    conflict: escalate
    preserve_on_regenerate: true
    template: |
      **Attack Surface:**
      - 
      **Mitigations:**
      -
---

# Security Review: ${target.name}

## Interface
<!-- source: ${target}#Interface -->

## Threat Model
<!-- editable -->
```

### Frontmatter Fields

| Field | Description |
|-------|-------------|
| `type` | Always `view-spec` |
| `name` | Human-readable name |
| `persona` | Who this view is for |
| `generation` | `dynamic` (auto) or `static` (manual) |
| `triggers` | When to regenerate |
| `instances.pattern` | Glob for target files |
| `sections` | Section definitions |

### Section Definition

| Field | Description |
|-------|-------------|
| `name` | Section heading |
| `source` | Input context mapping (where to get content) |
| `lock` | `readonly` or `editable` |
| `conflict` | `source-wins`, `merge`, or `escalate` |
| `preserve_on_regenerate` | Keep editable content on regenerate |
| `template` | Default content for editable sections |

## Input Context Mapping

How to specify where content comes from:

### File Heading

```yaml
source: "specs/auth.spec.md#Interface"
# Extracts ## Interface section from the spec
```

### Heading with Subpath

```yaml
source: "specs/auth.spec.md#Interface/Methods"
# Extracts ### Methods under ## Interface
```

### Entire File

```yaml
source: "specs/auth.spec.md"
# Entire file content
```

### Code Symbol (via LSP)

```yaml
source: "src/auth.ts::AuthService"
# Extract AuthService class

source: "src/auth.ts::authenticate()"
# Extract authenticate function
```

### JSON/YAML Path

```yaml
source: "package.json$.dependencies"
# Extract dependencies object

source: "config.yaml$.database.host"
# Extract specific config value
```

### Multiple Sources

```yaml
source:
  - "specs/auth.spec.md#Interface"
  - "specs/user.spec.md#Interface"
# Concatenated with metadata separators
```

## View Instance Format

Generated view instances:

```yaml
# .g5/views/security-review--auth.view.md
---
view_spec: specs/views/security-review.view-spec.md
target: specs/auth.spec.md
generated_at: 2026-01-10T10:00:00Z
source_hashes:
  "specs/auth.spec.md#interface": "abc123"
---

## Interface
<!-- lock: readonly, conflict: source-wins -->
(imported content from spec)

## Threat Model
<!-- lock: editable, conflict: escalate -->
**Attack Surface:**
- JWT tokens in local storage

**Mitigations:**
- Move to httpOnly cookies
```

## Lock Modes

| Mode | Behavior |
|------|----------|
| `readonly` | Cannot edit, always synced from source |
| `editable` | Can edit, conflicts possible |

## Conflict Strategies

| Strategy | Behavior |
|----------|----------|
| `source-wins` | Source changes overwrite view content |
| `merge` | 3-way merge using git history |
| `escalate` | Mark conflict, notify via Prism |

### Conflict Markers

When merge fails or escalation needed:

```markdown
<<<<<<< VIEW (your changes)
- JWT in localStorage is a security risk
=======
- JWT storage needs review
>>>>>>> SOURCE (incoming changes)
```

## Trigger Rules

When views auto-regenerate:

```yaml
triggers:
  - on: file_added
    pattern: "specs/**/*.spec.md"
    
  - on: file_changed
    pattern: "specs/**/*.spec.md"
    
  - on: workflow_complete
  
  - on: manual  # Only on explicit request
```

## Creating a View

### 1. Create View Spec

```markdown
# .g5/views/specs/code-review.view-spec.md
---
type: view-spec
name: Code Review
persona: Developer
generation: dynamic

instances:
  pattern: "src/**/*.py"

sections:
  - name: "Code"
    source: "${target}"
    lock: readonly
    conflict: source-wins
    
  - name: "Review Notes"
    lock: editable
    conflict: merge
    template: |
      **Observations:**
      -
      **Suggestions:**
      -
---

# Code Review: ${target.name}

## Code
<!-- source: ${target} -->

## Review Notes
<!-- editable -->
```

### 2. Generate Instance

The system generates instances for each matching target:
- `code-review--src-auth-py.view.md`
- `code-review--src-user-py.view.md`

### 3. Edit Editable Sections

Users can edit `editable` sections. Content is preserved on regenerate.

### 4. Sync on Source Change

When source changes:
- `readonly` sections: updated automatically
- `editable` sections: conflict resolution per strategy

## Key Operations

| Operation | Description |
|-----------|-------------|
| **Generate** | Create view instance from spec + target |
| **Sync** | Update readonly sections from sources |
| **Regenerate** | Full rebuild, preserve editable content |
| **Reformat** | Normalize markdown (idempotent) |
| **Compile** | Git diff + view → new workflow |

## Compile Flow

When view is edited:

```
User edits view
    │
    ▼
[Reformat] (normalize markdown)
    │
    ▼
[Compile] 
    │
    ▼
New workflow created with:
  - Git diff of view changes
  - Full view content as context
    │
    ▼
Workflow updates source artifacts
    │
    ▼
Views re-synchronized
```

## Common Mistakes

1. **Editing readonly sections** - Changes will be lost on sync
2. **Wrong source path** - Verify path and heading exist
3. **Missing preserve_on_regenerate** - Editable content lost on regenerate
4. **Ignoring conflicts** - Resolve conflict markers
5. **Wrong conflict strategy** - Use `escalate` for important editable content

## Debugging Views

### Check Source Hash

```yaml
# In view instance frontmatter
source_hashes:
  "specs/auth.spec.md#interface": "abc123"
```

If hash changes, sync is triggered.

### Verify Source Exists

```bash
# Check if source heading exists
grep -n "## Interface" specs/auth.spec.md
```

### Check View Status

```python
# In state.sqlite
state.get("views.instances")
# Shows status: synced | dirty | conflict
```

> 💡 **Related skills**: 
> - [g5-spec-writing](../g5-spec-writing/SKILL.md) for source specs
> - [g5-prism-web-design](../g5-prism-web-design/SKILL.md) for views UI
> - [g5-design](../g5-design/SKILL.md) for design docs (not views)
