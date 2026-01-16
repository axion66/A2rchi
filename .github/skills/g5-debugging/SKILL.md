---
name: g5-debugging
description: Guide for debugging test failures, autofix loops, and Docker testing in Phase 4. Use when tests are failing, stuck in autofix loops, need to run tests in Docker, or troubleshooting spec-code sync issues.
---

# G5 Debugging

This skill guides you through debugging in Phase 4 (Verify).

## When to Use This Skill

- Tests are failing
- Stuck in autofix loop (tried 3+ times)
- Need to run tests in Docker
- Spec-code sync issues
- Verification gate failing

## Docker Test Execution (REQUIRED)

**ALWAYS use Docker to run tests.** Never use the host system's Python/pytest directly.

### Why Docker?

- Host may have wrong Python version
- Missing or mismatched packages
- Inconsistent environment
- "Works on my machine" issues

### Running Tests

```bash
# Python tests (G5 core)
docker run --rm -v "$(pwd)":/workspace g5-runtime \
  python -m pytest /workspace/src/g5/tests/ -v --tb=short

# Run specific test file
docker run --rm -v "$(pwd)":/workspace g5-runtime \
  python -m pytest /workspace/src/g5/tests/test_state_store.py -v

# Run specific test
docker run --rm -v "$(pwd)":/workspace g5-runtime \
  python -m pytest /workspace/src/g5/tests/test_state_store.py::test_get_set -v
```

### Building the Docker Image

If the image doesn't exist:

```bash
cd src/prism && docker build -t g5-runtime -f docker/Dockerfile .
```

### TypeScript/Prism Tests

```bash
# Compile TypeScript
cd src/prism && npm run compile

# Run extension tests
cd src/prism && npm test
```

## Autofix Loop Protocol

When tests fail, you get 3 autofix attempts:

```
Test Failure
    │
    ▼
Attempt 1: Analyze error, fix code
    │
    ▼
Still failing?
    │
    ├── No → Done! ✓
    │
    └── Yes → Attempt 2
            │
            ▼
        Still failing?
            │
            ├── No → Done! ✓
            │
            └── Yes → Attempt 3
                    │
                    ▼
                Still failing?
                    │
                    ├── No → Done! ✓
                    │
                    └── Yes → GO BACK to Phase 2 or 3
```

### After 3 Failed Attempts

```javascript
// Spec is likely wrong
g5_goBackPhase({ 
  target_phase: 2, 
  reason: "Test failure indicates spec contract is incorrect: {specific issue}" 
})

// Or code approach is wrong
g5_goBackPhase({ 
  target_phase: 3, 
  reason: "Implementation approach flawed, need to reconsider design" 
})
```

## Test Failure Triage

### Step 1: Read the Error Carefully

```
FAILED test_state_store.py::test_get_returns_default
AssertionError: assert None == 'default_value'
```

Key info:
- Which test failed
- What was expected vs actual
- Stack trace location

### Step 2: Check Spec vs Expectation

Does the test match what the spec says?

```markdown
# From spec:
##### `get(key: str, default: Any = None) -> Any`
- POST: returns stored value or default if key not found
```

If test expects something different from spec → Fix test
If test matches spec → Fix code

### Step 3: Check Code vs Spec

Does the code match the spec signature and contracts?

```python
# Spec says: get(key: str, default: Any = None) -> Any
# Code has:
def get(self, key: str) -> Any:  # ❌ Missing default parameter!
```

### Step 4: Identify Root Cause

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| Wrong return value | Logic error | Fix code |
| Missing method | Incomplete implementation | Add method |
| Wrong error type | Error handling wrong | Fix error class |
| Signature mismatch | Code doesn't match spec | Fix code OR go back to fix spec |
| Test expects wrong thing | Test doesn't match spec | Fix test |

## Common Test Failures

### 1. Import Errors

```
ModuleNotFoundError: No module named 'g5.mcp.state_store'
```

**Fix**: Check file exists, check `__init__.py`, check PYTHONPATH in Docker

### 2. Assertion Errors

```
AssertionError: assert 'error' == 'success'
```

**Fix**: Trace through code, check conditionals, verify logic

### 3. Type Errors

```
TypeError: get() takes 2 positional arguments but 3 were given
```

**Fix**: Match signature to spec exactly

### 4. Attribute Errors

```
AttributeError: 'StateStore' object has no attribute 'connection'
```

**Fix**: Initialize attribute in `__init__`

### 5. Missing Error Handling

```
Expected UserNotFoundError but no exception was raised
```

**Fix**: Add error condition from spec

## Spec-Code Sync Recovery

When specs and code are out of sync:

### 1. Identify Which is Correct

Usually the spec is authoritative. But sometimes code reveals spec is wrong.

### 2. If Spec is Correct

Regenerate/fix code to match spec:

```javascript
// Stay in Phase 3/4 and fix code
```

### 3. If Code is Correct

Go back and update spec:

```javascript
g5_goBackPhase({ 
  target_phase: 2, 
  reason: "Code behavior is correct, spec needs to be updated to match" 
})
```

### 4. If Unclear

Ask the user:

```
🚨 Spec-code mismatch detected:

Spec says: `get()` returns `None` for missing keys
Code does: `get()` raises `KeyError` for missing keys

Which is correct?
1. Spec (return None) - I'll fix the code
2. Code (raise error) - I'll fix the spec
```

## Debugging Strategies

### Print Debugging

```python
def get(self, key: str, default: Any = None) -> Any:
    print(f"DEBUG: get called with key={key}, default={default}")
    result = self._data.get(key, default)
    print(f"DEBUG: returning {result}")
    return result
```

### Using pytest --pdb

```bash
docker run -it --rm -v "$(pwd)":/workspace g5-runtime \
  python -m pytest /workspace/src/g5/tests/test_state_store.py -v --pdb
```

### Checking Test Isolation

```bash
# Run single test
docker run --rm -v "$(pwd)":/workspace g5-runtime \
  python -m pytest /workspace/src/g5/tests/test_state_store.py::test_specific -v

# Run all tests to check for interaction issues
docker run --rm -v "$(pwd)":/workspace g5-runtime \
  python -m pytest /workspace/src/g5/tests/ -v
```

## Verification Gate Checklist

Before `CODE_TO_VERIFY` gate:

- [ ] All source files from spec exist
- [ ] Code compiles/imports without error
- [ ] All tests written
- [ ] Tests run (even if some fail)

Before `WORKFLOW_COMPLETE` gate:

- [ ] All tests pass
- [ ] No linting errors
- [ ] Spec-code sync verified
- [ ] No pending blockers

## When to Escalate

Stop debugging and ask for help when:

- 🚨 Test failure doesn't make sense (possible spec bug)
- 🚨 Spec and code fundamentally contradict
- 🚨 External dependency issue
- 🚨 Environment problem (Docker, permissions)
- 🚨 >3 autofix attempts without progress

> 💡 **Related skills**: 
> - [g5-testgen](../g5-testgen/SKILL.md) for writing tests
> - [g5-workflow-guidance](../g5-workflow-guidance/SKILL.md) for going back
> - [g5-codegen](../g5-codegen/SKILL.md) for fixing implementation
