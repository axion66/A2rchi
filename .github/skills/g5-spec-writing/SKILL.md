---
name: g5-spec-writing
description: Guide for writing G5 specs with contracts, invariants, and testing requirements. Use when creating or editing .spec.md files, defining interfaces, writing contracts, or specifying testing requirements.
---

# G5 Spec Writing

This skill guides you through writing high-quality specs in Phase 2.

## When to Use This Skill

- Creating a new `.spec.md` file
- Updating an existing spec
- Defining interfaces and contracts
- Specifying testing requirements

## Spec File Structure

```markdown
---
component_id: unique/path/id
type: component | file | system | module
parent_spec_id: parent/spec  # optional
dependencies:
  - dep/one
  - dep/two
source_files:
  - src/path/to/file.py
  - src/path/to/other.py
test_file: tests/test_component.py
---

# Component Name

## Overview

{What this component does, its purpose, key responsibilities}

## Design Principles

1. {Guiding principle 1}
2. {Guiding principle 2}

## Structured Design Doc

### Classes

#### ClassName

{Purpose of this class}

**Attributes:**
- `attribute_name: Type` - Description

**Methods:**

##### `method_name(param: Type) -> ReturnType`

{What this method does}

**Contracts:**
- PRE: {precondition}
- POST: {postcondition}
- ERROR: `ErrorType` when {condition}

## Guardrails

- {Constraint that must always be true}
- {Invariant the code must maintain}

## Testing Contracts

- {What tests must verify}
- {Edge cases to cover}
```

## YAML Frontmatter

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `component_id` | Unique identifier | `core/auth/service` |
| `type` | Component type | `component`, `file`, `system`, `module` |
| `source_files` | Files implementing this spec | `["src/auth.py"]` |

### Optional Fields

| Field | Description | Example |
|-------|-------------|---------|
| `parent_spec_id` | Parent spec (for hierarchy) | `core/auth` |
| `dependencies` | Specs this depends on | `["core/db", "utils/crypto"]` |
| `test_file` | Test file for this spec | `tests/test_auth.py` |

### Example Frontmatter

```yaml
---
component_id: state/state_store
type: component
dependencies:
  - state/state_schema
source_files:
  - src/g5/mcp/state_store.py
test_file: src/g5/tests/test_state_store.py
---
```

## Writing Contracts

Contracts define the formal behavior of methods.

### Preconditions (PRE)

What must be true **before** calling:

```markdown
- PRE: `user_id` is not None
- PRE: `amount > 0`
- PRE: File at `path` exists
- PRE: User is authenticated
```

### Postconditions (POST)

What will be true **after** successful execution:

```markdown
- POST: Returns user object with `id` field populated
- POST: Account balance decreased by `amount`
- POST: File is created at specified path
- POST: `state.phase` incremented by 1
```

### Error Conditions (ERROR)

What errors can occur and when:

```markdown
- ERROR: `UserNotFoundError` when user_id doesn't exist in database
- ERROR: `InsufficientFundsError` when balance < amount
- ERROR: `FileExistsError` when file already exists and overwrite=False
- ERROR: `ValidationError` when input fails schema validation
```

### Complete Contract Example

```markdown
##### `transfer(from_account: str, to_account: str, amount: Decimal) -> Transaction`

Transfer funds between accounts.

**Contracts:**
- PRE: `from_account` exists in database
- PRE: `to_account` exists in database
- PRE: `amount > 0`
- PRE: `from_account.balance >= amount`
- POST: `from_account.balance` decreased by `amount`
- POST: `to_account.balance` increased by `amount`
- POST: Returns `Transaction` with status="completed"
- ERROR: `AccountNotFoundError` when either account doesn't exist
- ERROR: `InsufficientFundsError` when from_account.balance < amount
- ERROR: `InvalidAmountError` when amount <= 0
```

## Structured Design Doc Section

This section defines the implementation interface.

### Classes

For each class, define:
1. **Purpose** - One sentence description
2. **Attributes** - Name, type, description
3. **Methods** - Full signatures with contracts

### Method Signatures

Be **exact** - code must match these precisely:

```markdown
##### `method_name(param1: Type1, param2: Type2 = default) -> ReturnType`
```

Include:
- Exact method name
- All parameters with types
- Default values if any
- Return type

### Enums and Constants

```markdown
### Enums

#### PhaseType
- `INTENT = 1`
- `SPEC = 2`
- `CODE = 3`
- `VERIFY = 4`

### Constants

- `MAX_RETRIES = 3`
- `DEFAULT_TIMEOUT = 30`
```

## Guardrails Section

Constraints and invariants:

```markdown
## Guardrails

- Phase number must be 1-4 inclusive
- Cannot advance phase without passing gate
- Workflow ID must be unique
- State file must always be valid YAML
- Backward navigation cannot go to Phase 4
```

These become validation checks in code.

## Testing Contracts Section

**⚠️ CANONICAL FORMAT**: Testing contracts MUST use this exact format for G5 tooling to extract them:

```markdown
## Contracts

### TC1: Create task with defaults
- PRE: slug is unique, not empty
- POST: Task created with phase=1, status='active'
- POST: branch set to 'g5/{slug}'
- ERROR: DuplicateSlugError if slug exists

### TC2: Advance phase
- PRE: current_phase < 4
- POST: current_phase incremented by 1
- POST: navigation_history updated

### TC3: Complete workflow
- PRE: current_phase == 4
- PRE: all tests passing
- POST: task_status set to 'completed'
- POST: archived_state contains state snapshot
```

**Rules:**
1. Section MUST be titled `## Contracts` (exact heading)
2. Each contract MUST use `### TC{N}: {description}` format
3. TC numbers should be sequential (TC1, TC2, TC3...)
4. Contract body contains PRE/POST/ERROR bullet points
5. Keep descriptions concise (one line)

**Why this format?**
- G5 extracts contracts automatically from specs
- Contracts appear in Testing Dashboard
- Future: Contract-to-test coverage tracking

## Dependency Order

When multiple specs need updates, process in **dependency order** (leaves first):

```
1. No dependencies → process first
2. Has dependencies → process after dependencies done
```

Example order:
1. `utils/validation.spec.md` (no deps)
2. `state/schema.spec.md` (no deps)
3. `state/store.spec.md` (depends on schema)
4. `core/engine.spec.md` (depends on store)

## Common Mistakes

1. **Vague methods** - "process data" → Be specific: "parse JSON input and validate against schema"
2. **Missing error conditions** - Always define what errors can occur
3. **Implementation in spec** - Don't include code, just interface
4. **Wrong types** - Use actual language types (`str`, `int`, `Optional[X]`)
5. **No test_file** - Required for `SPEC_TO_CODE` gate
6. **Incomplete contracts** - Every public method needs PRE/POST/ERROR

## Spec Validation Checklist

Before advancing to Phase 3:

- [ ] Frontmatter has `component_id`, `type`, `source_files`
- [ ] `test_file` is defined
- [ ] Every public method has a signature
- [ ] Every method has PRE/POST/ERROR contracts
- [ ] Guardrails section defines constraints
- [ ] Testing contracts section exists
- [ ] Dependencies are listed if any

> 💡 **Related skills**: 
> - [g5-codegen](../g5-codegen/SKILL.md) for implementing specs
> - [g5-test-planning](../g5-test-planning/SKILL.md) for test strategy
> - See [examples/example-spec.md](./examples/example-spec.md) for a complete example
