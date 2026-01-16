---
name: g5-codegen
description: Guide for generating code from G5 specs. Use when implementing code from specs in Phase 3, matching spec signatures, implementing contracts, and writing code that exactly matches the Structured Design Doc.
---

# G5 Code Generation

This skill guides you through implementing code that exactly matches specs in Phase 3.

## When to Use This Skill

- Implementing code from a spec
- Need to match spec signatures exactly
- Implementing contracts as validation
- Writing code that follows the Structured Design Doc

## The Golden Rule

**Implement EXACTLY what the spec specifies.**

- Same class names
- Same method names
- Same parameter names and types
- Same return types
- All guardrails as validation

## Step-by-Step Process

### 1. Read the Spec

Before writing any code:

```bash
# Find the governing spec
cat .g5/specs/{component}.spec.md
# or
cat src/g5/specs/{path}/component.spec.md
```

Focus on:
- **Structured Design Doc** section (the interface)
- **Contracts** (PRE/POST/ERROR)
- **Guardrails** (constraints)

### 2. Create File Structure

Match the spec's `source_files`:

```yaml
# From spec frontmatter
source_files:
  - src/g5/mcp/state_store.py
```

Create the file at that exact path.

### 3. Implement Classes

For each class in the spec:

```python
# Spec says:
# #### StateStore
# A class that manages workflow state in SQLite.
# 
# **Attributes:**
# - `db_path: Path` - Path to SQLite database
# - `connection: Optional[Connection]` - Active connection

class StateStore:
    """A class that manages workflow state in SQLite."""
    
    def __init__(self, db_path: Path):
        self.db_path: Path = db_path
        self.connection: Optional[Connection] = None
```

### 4. Implement Method Signatures

Match signatures **exactly**:

```python
# Spec says:
# ##### `get(key: str, default: Any = None) -> Any`

def get(self, key: str, default: Any = None) -> Any:
    ...
```

**Common mistakes:**
- ❌ `def get(self, k, d=None)` - Wrong parameter names
- ❌ `def get(self, key: str)` - Missing default parameter
- ❌ `def get_value(...)` - Wrong method name

### 5. Implement Contracts

#### Preconditions → Validation at Start

```python
# Spec: PRE: `key` is not empty
# Spec: PRE: `amount > 0`

def transfer(self, key: str, amount: Decimal) -> None:
    # Implement preconditions as validation
    if not key:
        raise ValueError("key cannot be empty")
    if amount <= 0:
        raise ValueError("amount must be positive")
    
    # ... rest of implementation
```

#### Postconditions → Ensure Results

```python
# Spec: POST: Returns user with `id` field populated

def create_user(self, name: str) -> User:
    user = User(name=name)
    self.db.save(user)
    
    # Ensure postcondition
    assert user.id is not None, "User id must be populated"
    return user
```

#### Error Conditions → Raise Specific Errors

```python
# Spec: ERROR: `UserNotFoundError` when user_id doesn't exist

def get_user(self, user_id: str) -> User:
    user = self.db.find(user_id)
    if user is None:
        raise UserNotFoundError(f"User {user_id} not found")
    return user
```

### 6. Implement Guardrails

```python
# Spec Guardrail: Phase number must be 1-4 inclusive

def set_phase(self, phase: int) -> None:
    if not 1 <= phase <= 4:
        raise ValueError(f"Phase must be 1-4, got {phase}")
    self._phase = phase
```

### 7. Add Spec References

Comment where code implements spec elements:

```python
class StateStore:
    """
    Manages workflow state in SQLite.
    
    Implements: state/state_store.spec.md
    """
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from state.
        
        Contracts:
        - PRE: key is valid string
        - POST: returns stored value or default
        - ERROR: StateError on database failure
        """
        ...
```

## Language-Specific Patterns

### Python

```python
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class Config:
    """Matches spec's Config class."""
    name: str
    value: int
    enabled: bool = True

def process(items: List[str]) -> Dict[str, Any]:
    """
    Process items according to spec.
    
    PRE: items is not empty
    POST: returns dict with 'count' and 'results' keys
    """
    if not items:
        raise ValueError("items cannot be empty")
    
    results = [transform(item) for item in items]
    
    return {
        "count": len(results),
        "results": results
    }
```

### TypeScript

```typescript
interface Config {
  name: string;
  value: number;
  enabled?: boolean;
}

/**
 * Process items according to spec.
 * 
 * @param items - List of items to process
 * @returns Object with count and results
 * @throws Error if items is empty
 */
function process(items: string[]): { count: number; results: string[] } {
  // PRE: items is not empty
  if (items.length === 0) {
    throw new Error("items cannot be empty");
  }
  
  const results = items.map(transform);
  
  // POST: returns dict with count and results
  return {
    count: results.length,
    results
  };
}
```

## Dependency Order

Process specs **leaves first** (no dependencies before dependencies):

```
Spec Dependency Graph:
  utils/validation (no deps) ← Process 1st
  state/schema (no deps) ← Process 2nd  
  state/store (depends on schema) ← Process 3rd
  core/engine (depends on store) ← Process 4th
```

## Common Mistakes

1. **Changing signatures** - Must match spec exactly
2. **Skipping preconditions** - All PRE conditions must be validated
3. **Wrong error types** - Use exact error class from spec
4. **Adding methods** - Don't add methods not in spec
5. **Missing type hints** - Include all types from spec
6. **Forgetting defaults** - Include default values exactly as specified

## Code Review Checklist

Before moving to Phase 4:

- [ ] All classes from spec are implemented
- [ ] All method signatures match exactly
- [ ] All preconditions validated at method start
- [ ] All error conditions raise correct error types
- [ ] All guardrails enforced
- [ ] Type hints match spec
- [ ] Spec reference in docstring/comments

## When Spec is Wrong

If you discover the spec is incorrect during implementation:

```javascript
g5_goBackPhase({ 
  target_phase: 2, 
  reason: "Spec missing error handling for null input case" 
})
```

**Don't** implement something different from the spec. **Do** go back and fix the spec first.

> 💡 **Related skills**: 
> - [g5-spec-writing](../g5-spec-writing/SKILL.md) for understanding spec format
> - [g5-testgen](../g5-testgen/SKILL.md) for writing tests alongside code
> - [g5-debugging](../g5-debugging/SKILL.md) when tests fail
