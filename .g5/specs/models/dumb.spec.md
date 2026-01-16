---
type: spec
module: a2rchi.models.dumb
version: "1.0"
status: extracted
test_file: tests/unit/test_models_dumb.py
source_files:
  - src/a2rchi/models/dumb.py
---

# Dumb LLM Spec

## Overview

A simple mock LLM for testing purposes. Returns random responses after a configurable delay, useful for testing the full pipeline without expensive model calls.

## Dependencies

- `src/a2rchi/models/base.BaseCustomLLM` - Abstract base class
- `src/utils/logging` - Logging utilities
- `numpy` - Random number generation
- `time` - Sleep functionality

## Public API

### Classes

#### `DumbLLM`
```python
class DumbLLM(BaseCustomLLM):
    """A simple Dumb LLM, perfect for testing."""
    
    filler: str = None               # Unused placeholder
    sleep_time_mean: int = 3         # Mean sleep time in seconds
```

**Methods:**

##### `_call`
```python
def _call(self, prompt: str = None, stop: Optional[List[str]] = None) -> str
```

Return a random response after sleeping.

**Contracts:**
- ENSURES: Sleeps for `N(sleep_time_mean, 1)` seconds (normal distribution)
- ENSURES: Logs sleep duration
- ENSURES: Returns fixed message with random 5-digit number
- ENSURES: Ignores `prompt` and `stop` parameters

**Return Format:**
```
"I am just a dumb LLM, I will give you a number: {random_5_digit}"
```

## Behavior

1. Generate sleep time from normal distribution: `N(mean=3, std=1)`
2. Log the sleep time
3. Sleep for that duration
4. Return fixed message with random number between 10000-99999

## Use Cases

- **Unit testing**: Test pipeline without model dependencies
- **Integration testing**: Verify request handling
- **Load testing**: Simulate model latency
- **Development**: Fast iteration without GPU

## Example

```python
llm = DumbLLM(sleep_time_mean=1)  # Faster for tests
response = llm._call("Any prompt is ignored")
# After ~1 second:
# "I am just a dumb LLM, I will give you a number: 42387"
```

## Invariants

1. Response is always the same format
2. Sleep time varies but averages to `sleep_time_mean`
3. Prompt content is completely ignored
4. Stop tokens are ignored
