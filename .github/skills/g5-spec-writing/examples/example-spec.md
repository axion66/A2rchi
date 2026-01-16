---
component_id: example/calculator
type: component
dependencies: []
source_files:
  - src/calculator.py
test_file: tests/test_calculator.py
---

# Calculator

## Overview

A simple calculator component that performs basic arithmetic operations. Demonstrates proper spec structure with contracts.

## Design Principles

1. **Explicit over implicit** - All operations clearly defined
2. **Fail fast** - Invalid inputs raise errors immediately
3. **Immutable** - Operations return new values, don't modify state

## Structured Design Doc

### Classes

#### Calculator

A stateless calculator that performs arithmetic operations.

**Attributes:**
- `precision: int` - Decimal places for rounding (default: 2)

**Methods:**

##### `__init__(precision: int = 2) -> None`

Initialize calculator with specified precision.

**Contracts:**
- PRE: `precision >= 0`
- POST: `self.precision == precision`
- ERROR: `ValueError` when precision < 0

##### `add(a: float, b: float) -> float`

Add two numbers.

**Contracts:**
- PRE: `a` and `b` are finite numbers (not NaN or Inf)
- POST: Returns `a + b` rounded to `self.precision`
- ERROR: `ValueError` when inputs are NaN or Inf

##### `subtract(a: float, b: float) -> float`

Subtract b from a.

**Contracts:**
- PRE: `a` and `b` are finite numbers
- POST: Returns `a - b` rounded to `self.precision`
- ERROR: `ValueError` when inputs are NaN or Inf

##### `multiply(a: float, b: float) -> float`

Multiply two numbers.

**Contracts:**
- PRE: `a` and `b` are finite numbers
- POST: Returns `a * b` rounded to `self.precision`
- ERROR: `ValueError` when inputs are NaN or Inf

##### `divide(a: float, b: float) -> float`

Divide a by b.

**Contracts:**
- PRE: `a` and `b` are finite numbers
- PRE: `b != 0`
- POST: Returns `a / b` rounded to `self.precision`
- ERROR: `ZeroDivisionError` when b == 0
- ERROR: `ValueError` when inputs are NaN or Inf

### Enums

*None*

### Constants

- `DEFAULT_PRECISION = 2`

## Guardrails

- Precision must be non-negative
- All inputs must be finite numbers
- Division by zero is not allowed
- Results are always rounded to specified precision

## Testing Contracts

- `add`: verify commutativity (a + b == b + a)
- `subtract`: verify a - b != b - a for a != b
- `multiply`: verify commutativity and identity (a * 1 == a)
- `divide`: verify a / 1 == a, error on b == 0
- All operations: verify NaN/Inf rejection
- Precision: verify rounding works correctly
- Edge cases: very large numbers, very small numbers, negative zero
