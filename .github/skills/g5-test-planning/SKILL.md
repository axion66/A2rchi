---
name: g5-test-planning
description: Guide for planning test strategy from spec contracts. Use when determining what tests to write, identifying test cases from contracts, planning test coverage, and creating test strategy during Phase 2.
---

# G5 Test Planning

This skill guides you through planning tests from spec contracts.

## When to Use This Skill

- Planning what tests to write
- Identifying test cases from contracts
- Determining test coverage strategy
- Setting up `test_file` in spec frontmatter

## Contract-to-Test Mapping

Every contract element maps to tests:

| Contract Type | Test Type | Example |
|---------------|-----------|---------|
| PRE (precondition) | Validation test | Test that invalid input raises error |
| POST (postcondition) | Behavior test | Test that output matches expectation |
| ERROR | Error handling test | Test that specific error is raised |
| Guardrail | Constraint test | Test that invariant is maintained |

## Step-by-Step Process

### 1. Extract Contracts from Spec

From a spec method:

```markdown
##### `transfer(from_acct: str, to_acct: str, amount: Decimal) -> Transaction`

**Contracts:**
- PRE: `from_acct` exists in database
- PRE: `to_acct` exists in database  
- PRE: `amount > 0`
- PRE: `from_acct.balance >= amount`
- POST: `from_acct.balance` decreased by `amount`
- POST: `to_acct.balance` increased by `amount`
- POST: Returns `Transaction` with status="completed"
- ERROR: `AccountNotFoundError` when either account doesn't exist
- ERROR: `InsufficientFundsError` when balance < amount
- ERROR: `InvalidAmountError` when amount <= 0
```

### 2. Create Test Cases

**From PRE conditions** (validation tests):

```python
def test_transfer_rejects_nonexistent_from_account():
    """PRE: from_acct exists in database"""
    
def test_transfer_rejects_nonexistent_to_account():
    """PRE: to_acct exists in database"""
    
def test_transfer_rejects_zero_amount():
    """PRE: amount > 0"""
    
def test_transfer_rejects_negative_amount():
    """PRE: amount > 0"""
    
def test_transfer_rejects_insufficient_balance():
    """PRE: from_acct.balance >= amount"""
```

**From POST conditions** (behavior tests):

```python
def test_transfer_decreases_from_balance():
    """POST: from_acct.balance decreased by amount"""
    
def test_transfer_increases_to_balance():
    """POST: to_acct.balance increased by amount"""
    
def test_transfer_returns_completed_transaction():
    """POST: Returns Transaction with status=completed"""
```

**From ERROR conditions** (error tests):

```python
def test_transfer_raises_account_not_found_for_missing_from():
    """ERROR: AccountNotFoundError when from_acct doesn't exist"""
    
def test_transfer_raises_account_not_found_for_missing_to():
    """ERROR: AccountNotFoundError when to_acct doesn't exist"""
    
def test_transfer_raises_insufficient_funds():
    """ERROR: InsufficientFundsError when balance < amount"""
    
def test_transfer_raises_invalid_amount_for_zero():
    """ERROR: InvalidAmountError when amount <= 0"""
```

### 3. Add Edge Cases

Beyond contracts, test edge cases:

```python
def test_transfer_exact_balance():
    """Edge: transfer entire balance (balance == amount)"""
    
def test_transfer_self():
    """Edge: transfer to same account"""
    
def test_transfer_minimum_amount():
    """Edge: smallest valid amount"""
    
def test_transfer_large_amount():
    """Edge: very large amount"""
```

### 4. Add Integration Tests

Test cross-component behavior:

```python
def test_transfer_persists_after_restart():
    """Integration: balances correct after DB reconnect"""
    
def test_concurrent_transfers():
    """Integration: multiple transfers don't corrupt state"""
```

## Test Categories

### Unit Tests (Single Contract)

Test one method, one contract at a time:

```python
class TestCalculatorAdd:
    def test_add_positive_numbers(self):
        """POST: returns a + b"""
        
    def test_add_rejects_nan(self):
        """ERROR: ValueError when input is NaN"""
```

### Contract Tests (All Contracts for Method)

Group all contracts for a method:

```python
class TestTransferContracts:
    """All contracts for transfer() method"""
    
    # PRE tests
    def test_pre_from_account_exists(self): ...
    def test_pre_to_account_exists(self): ...
    def test_pre_amount_positive(self): ...
    def test_pre_sufficient_balance(self): ...
    
    # POST tests
    def test_post_from_balance_decreased(self): ...
    def test_post_to_balance_increased(self): ...
    def test_post_returns_transaction(self): ...
    
    # ERROR tests
    def test_error_account_not_found(self): ...
    def test_error_insufficient_funds(self): ...
```

### Integration Tests (Cross-Spec)

Test interactions between components:

```python
class TestStateStoreEngineIntegration:
    """StateStore + Engine integration"""
    
    def test_engine_uses_store_correctly(self): ...
    def test_state_persists_across_phases(self): ...
```

## Test File Setup

### Spec Frontmatter

```yaml
---
component_id: core/calculator
source_files:
  - src/calculator.py
test_file: tests/test_calculator.py  # ← Required for SPEC_TO_CODE gate
---
```

### Test File Structure

```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── test_calculator.py    # Matches spec's test_file
├── test_state_store.py
└── integration/
    └── test_full_workflow.py
```

## Test Naming Convention

```python
def test_{method}_{scenario}():
    """
    Format: test_{what}_{condition/expectation}
    
    Examples:
    - test_add_positive_numbers
    - test_add_rejects_nan_input
    - test_transfer_insufficient_funds_raises_error
    """
```

## Coverage Goals

| Priority | Coverage Type | Target |
|----------|--------------|--------|
| P0 | All ERROR conditions | 100% |
| P0 | All PRE conditions | 100% |
| P1 | All POST conditions | 100% |
| P1 | Happy path | 100% |
| P2 | Edge cases | 80%+ |
| P3 | Integration | Key paths |

## Test Planning Checklist

Before Phase 3:

- [ ] Every method has test cases identified
- [ ] Every PRE condition has validation test
- [ ] Every POST condition has behavior test
- [ ] Every ERROR condition has error test
- [ ] Edge cases identified
- [ ] `test_file` set in spec frontmatter
- [ ] Test file structure planned

## Common Mistakes

1. **Testing implementation, not contract** - Test behavior, not how it's done
2. **Missing error tests** - Every ERROR needs a test
3. **No edge cases** - Empty, null, boundary values
4. **Test not matching spec** - Test must verify spec contracts
5. **Forgetting test_file** - Required for gate

> 💡 **Related skills**: 
> - [g5-spec-writing](../g5-spec-writing/SKILL.md) for writing contracts
> - [g5-testgen](../g5-testgen/SKILL.md) for implementing tests
> - [g5-debugging](../g5-debugging/SKILL.md) when tests fail
