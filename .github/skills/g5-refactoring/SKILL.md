---
name: g5-refactoring
description: Guide for refactoring code while maintaining spec-code sync. Use when restructuring code, renaming components, extracting classes, or any refactoring that might affect specs.
---

# G5 Refactoring

This skill guides you through refactoring while maintaining spec-code sync.

## When to Use This Skill

- Restructuring code
- Renaming classes, methods, or files
- Extracting classes or functions
- Any change that might affect spec signatures

## The Key Question

**Does this refactor change the spec's Structured Design Doc?**

| Answer | Action |
|--------|--------|
| YES | Update spec FIRST, then refactor code |
| NO | Refactor code directly |

## Safe Refactors (No Spec Change)

These don't change the public interface:

### Extract Internal Method

```python
# Before
def process(self, data):
    # 50 lines of code
    result = complex_calculation(data)
    # more code
    return result

# After - extract internal helper
def process(self, data):
    intermediate = self._step_one(data)
    result = self._step_two(intermediate)
    return result

def _step_one(self, data):  # Internal, not in spec
    ...

def _step_two(self, data):  # Internal, not in spec
    ...
```

✅ Safe: Internal methods (prefixed with `_`) aren't in spec.

### Rename Local Variables

```python
# Before
def calculate(self, x, y):
    t = x + y
    r = t * 2
    return r

# After
def calculate(self, x, y):
    total = x + y
    result = total * 2
    return result
```

✅ Safe: Local variables aren't in spec.

### Simplify Conditionals

```python
# Before
def is_valid(self, value):
    if value is None:
        return False
    if value < 0:
        return False
    return True

# After
def is_valid(self, value):
    return value is not None and value >= 0
```

✅ Safe: Behavior unchanged, signature unchanged.

### Remove Dead Code

```python
# Before
def process(self, data):
    result = transform(data)
    # unused_value = old_calculation(data)  # Remove this
    return result
```

✅ Safe: Removing unused code doesn't affect interface.

## Spec-Changing Refactors

These REQUIRE spec update first:

### Rename Public Method

```markdown
# Spec change required:
##### `calculate(x: int, y: int) -> int`  # OLD
##### `compute(x: int, y: int) -> int`    # NEW
```

Then update code:
```python
# def calculate(self, x: int, y: int) -> int:  # OLD
def compute(self, x: int, y: int) -> int:      # NEW
```

### Change Signature

```markdown
# Spec change required:
##### `process(data: str) -> Result`                    # OLD
##### `process(data: str, options: Options) -> Result`  # NEW
```

### Extract Class

```markdown
# Spec change required:
# OLD: One class with many responsibilities
#### DataProcessor
  - `load(path)` 
  - `validate(data)`
  - `transform(data)`
  - `save(path, data)`

# NEW: Extracted into focused classes
#### DataLoader
  - `load(path)`
  - `save(path, data)`

#### DataValidator
  - `validate(data)`

#### DataTransformer
  - `transform(data)`
```

### Move Method to Different Class

```markdown
# Spec change required:
# Remove from ClassA, add to ClassB

#### ClassA
  # - `helper_method()` ← REMOVE

#### ClassB
  - `helper_method()` ← ADD
```

## Refactoring Workflow

### For Safe Refactors

```
1. Identify refactor is safe (no interface change)
2. Make code changes
3. Run tests to verify behavior unchanged
4. Done
```

### For Spec-Changing Refactors

```
1. Identify spec needs updating
2. Go back to Phase 2 if needed:
   g5_goBackPhase({ target_phase: 2, reason: "Refactoring requires spec update" })
3. Update spec with new interface
4. Advance to Phase 3
5. Update code to match new spec
6. Update tests for new interface
7. Verify all tests pass
```

## Common Refactoring Patterns

### Inline Method

**Safe** if method is internal:
```python
# Before
def process(self, x):
    return self._helper(x)

def _helper(self, x):
    return x * 2

# After
def process(self, x):
    return x * 2
```

### Replace Conditional with Polymorphism

**Spec-changing** - creates new classes:
```python
# Before (one class)
def process(self, item):
    if item.type == 'A':
        return self._process_a(item)
    elif item.type == 'B':
        return self._process_b(item)

# After (multiple classes) - UPDATE SPEC FIRST
class ProcessorA:
    def process(self, item): ...

class ProcessorB:
    def process(self, item): ...
```

### Extract Interface

**Spec-changing** - creates new abstraction:
```python
# Before
class ConcreteService:
    def do_thing(self): ...

# After - UPDATE SPEC FIRST
class IService(Protocol):  # New in spec
    def do_thing(self) -> None: ...

class ConcreteService(IService):
    def do_thing(self): ...
```

## Maintaining Sync

### Before Refactoring

```bash
# Check current sync status
g5_getPhaseContext
# Look at artifacts.specs to see what's tracked
```

### After Refactoring

```bash
# Verify code still matches spec
# Run tests
docker run --rm -v "$(pwd)":/workspace g5-runtime \
  python -m pytest /workspace/src/g5/tests/ -v
```

## Red Flags

Stop and reconsider when:

- 🚨 Changing method signature without spec update
- 🚨 Renaming public class without spec update
- 🚨 Removing method that's in spec
- 🚨 Adding method that's not in spec
- 🚨 Tests failing after "safe" refactor

## Decision Tree

```
Want to refactor code?
│
├── Does it change any signature in spec?
│   │
│   ├── YES → Go to Phase 2, update spec first
│   │
│   └── NO → Continue to next question
│
├── Does it add/remove public methods?
│   │
│   ├── YES → Go to Phase 2, update spec first
│   │
│   └── NO → Continue to next question
│
├── Does it change behavior (not just structure)?
│   │
│   ├── YES → Verify spec allows this behavior
│   │
│   └── NO → Safe to refactor
│
└── Proceed with refactor, run tests
```

## Common Mistakes

1. **Changing signatures without spec update** - Always spec first
2. **Assuming rename is safe** - Public renames need spec update
3. **Forgetting to run tests** - Always verify behavior unchanged
4. **Large refactors in one step** - Break into smaller changes
5. **Not going back to Phase 2** - Use `g5_goBackPhase` when needed

> 💡 **Related skills**: 
> - [g5-spec-writing](../g5-spec-writing/SKILL.md) for updating specs
> - [g5-codegen](../g5-codegen/SKILL.md) for implementing changes
> - [g5-workflow-guidance](../g5-workflow-guidance/SKILL.md) for phase navigation
