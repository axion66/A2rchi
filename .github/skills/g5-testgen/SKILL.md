---
name: g5-testgen
description: Guide for generating test files from spec contracts. Use when implementing tests in Phase 3, writing pytest tests, creating test fixtures, and generating test code from contracts.
---

# G5 Test Generation

This skill guides you through generating test files from spec contracts.

## When to Use This Skill

- Writing test implementations in Phase 3
- Need pytest patterns for contract testing
- Creating test fixtures
- Generating test code from spec contracts

## Test File Template

```python
"""
Tests for {ComponentName}

Spec: {path/to/spec.spec.md}
"""

import pytest
from typing import Any
from unittest.mock import Mock, patch

from module import ComponentName, SomeError


class TestComponentName:
    """Tests for ComponentName class."""
    
    @pytest.fixture
    def component(self) -> ComponentName:
        """Create a fresh component instance."""
        return ComponentName()
    
    # === PRE condition tests ===
    
    def test_method_rejects_invalid_input(self, component: ComponentName):
        """PRE: input must be valid"""
        with pytest.raises(ValueError, match="invalid input"):
            component.method(invalid_input)
    
    # === POST condition tests ===
    
    def test_method_returns_expected_result(self, component: ComponentName):
        """POST: returns expected result"""
        result = component.method(valid_input)
        assert result == expected_value
    
    # === ERROR condition tests ===
    
    def test_method_raises_specific_error(self, component: ComponentName):
        """ERROR: SomeError when condition"""
        with pytest.raises(SomeError) as exc_info:
            component.method(triggering_input)
        assert "expected message" in str(exc_info.value)
```

## Pytest Patterns

### Basic Assertion

```python
def test_add_returns_sum(self, calc: Calculator):
    """POST: returns a + b"""
    result = calc.add(2, 3)
    assert result == 5
```

### Testing Exceptions

```python
def test_divide_by_zero_raises(self, calc: Calculator):
    """ERROR: ZeroDivisionError when b == 0"""
    with pytest.raises(ZeroDivisionError):
        calc.divide(10, 0)

def test_divide_by_zero_message(self, calc: Calculator):
    """ERROR: ZeroDivisionError with message"""
    with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
        calc.divide(10, 0)
```

### Parametrized Tests

```python
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_add_various_inputs(self, calc: Calculator, a, b, expected):
    """POST: returns a + b for various inputs"""
    assert calc.add(a, b) == expected
```

### Testing Multiple Error Conditions

```python
@pytest.mark.parametrize("amount,error_type", [
    (0, InvalidAmountError),
    (-10, InvalidAmountError),
    (float('nan'), ValueError),
])
def test_transfer_invalid_amounts(self, bank, amount, error_type):
    """ERROR: various errors for invalid amounts"""
    with pytest.raises(error_type):
        bank.transfer("A", "B", amount)
```

## Fixtures

### Basic Fixture

```python
@pytest.fixture
def calculator() -> Calculator:
    """Create a calculator with default precision."""
    return Calculator(precision=2)

@pytest.fixture
def calculator_high_precision() -> Calculator:
    """Create a calculator with high precision."""
    return Calculator(precision=10)
```

### Fixture with Setup/Teardown

```python
@pytest.fixture
def state_store(tmp_path) -> StateStore:
    """Create a StateStore with temp database."""
    db_path = tmp_path / "test_state.sqlite"
    store = StateStore(db_path)
    store.initialize()
    yield store
    store.close()
```

### Shared Fixtures (conftest.py)

```python
# tests/conftest.py

import pytest
from pathlib import Path

@pytest.fixture
def temp_workspace(tmp_path) -> Path:
    """Create a temporary workspace structure."""
    (tmp_path / ".g5").mkdir()
    (tmp_path / ".g5" / "design_docs").mkdir()
    (tmp_path / ".g5" / "views").mkdir()
    return tmp_path

@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    return Mock()
```

## Testing Contracts

### PRE Condition Tests

For each precondition, test that violation raises an error:

```python
# Spec: PRE: key is not empty

def test_get_rejects_empty_key(self, store: StateStore):
    """PRE: key is not empty"""
    with pytest.raises(ValueError, match="key cannot be empty"):
        store.get("")

def test_get_rejects_none_key(self, store: StateStore):
    """PRE: key is not None"""
    with pytest.raises(ValueError):
        store.get(None)
```

### POST Condition Tests

For each postcondition, verify the result:

```python
# Spec: POST: returns stored value or default if key not found

def test_get_returns_stored_value(self, store: StateStore):
    """POST: returns stored value"""
    store.set("key", "value")
    assert store.get("key") == "value"

def test_get_returns_default_for_missing(self, store: StateStore):
    """POST: returns default if key not found"""
    assert store.get("missing", default="fallback") == "fallback"

def test_get_returns_none_default(self, store: StateStore):
    """POST: returns None as default"""
    assert store.get("missing") is None
```

### ERROR Condition Tests

For each error condition, verify the exact error type:

```python
# Spec: ERROR: UserNotFoundError when user_id doesn't exist

def test_get_user_raises_not_found(self, service: UserService):
    """ERROR: UserNotFoundError for missing user"""
    with pytest.raises(UserNotFoundError) as exc:
        service.get_user("nonexistent-id")
    
    assert "nonexistent-id" in str(exc.value)
```

## Mocking

### Mock Dependencies

```python
def test_service_calls_database(self):
    """Verify service uses database correctly."""
    mock_db = Mock()
    mock_db.find.return_value = {"id": "123", "name": "Test"}
    
    service = UserService(db=mock_db)
    result = service.get_user("123")
    
    mock_db.find.assert_called_once_with("123")
    assert result["name"] == "Test"
```

### Patch External Calls

```python
@patch('module.external_api.fetch')
def test_service_handles_api_failure(self, mock_fetch):
    """ERROR: ServiceError when API fails"""
    mock_fetch.side_effect = ConnectionError()
    
    service = MyService()
    with pytest.raises(ServiceError):
        service.fetch_data()
```

## Running Tests in Docker

**ALWAYS use Docker:**

```bash
# Run all tests
docker run --rm -v "$(pwd)":/workspace g5-runtime \
  python -m pytest /workspace/src/g5/tests/ -v --tb=short

# Run specific test file
docker run --rm -v "$(pwd)":/workspace g5-runtime \
  python -m pytest /workspace/src/g5/tests/test_calculator.py -v

# Run with coverage
docker run --rm -v "$(pwd)":/workspace g5-runtime \
  python -m pytest /workspace/src/g5/tests/ --cov=src/g5 --cov-report=term
```

## Test Organization

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_calculator.py       # Unit tests for Calculator spec
├── test_state_store.py      # Unit tests for StateStore spec
├── test_engine.py           # Unit tests for Engine spec
└── integration/
    ├── __init__.py
    └── test_workflow.py     # Cross-component tests
```

## Common Mistakes

1. **Not testing all contracts** - Every PRE/POST/ERROR needs a test
2. **Testing implementation details** - Test behavior, not internals
3. **Missing edge cases** - Empty, None, boundary values
4. **Not using fixtures** - Avoid setup duplication
5. **Running on host** - Always use Docker
6. **Weak assertions** - Be specific about expected values

## Test Generation Checklist

- [ ] Test file created at spec's `test_file` path
- [ ] All PRE conditions have validation tests
- [ ] All POST conditions have behavior tests
- [ ] All ERROR conditions have error tests
- [ ] Edge cases covered
- [ ] Fixtures created for setup
- [ ] Tests run in Docker

> 💡 **Related skills**: 
> - [g5-test-planning](../g5-test-planning/SKILL.md) for test strategy
> - [g5-debugging](../g5-debugging/SKILL.md) when tests fail
> - [g5-codegen](../g5-codegen/SKILL.md) for implementation
