---
type: spec
module: a2rchi.pipelines.classic_pipelines.utils.safety_checker
version: "1.0"
status: extracted
test_file: tests/unit/test_safety_checker.py
source_files:
  - src/a2rchi/pipelines/classic_pipelines/utils/safety_checker.py
---

# Safety Checker Utility Spec

## Overview

Wrapper function for running content through multiple safety checkers. Used by model classes to validate prompts and outputs.

## Dependencies

- `src/utils/logging`

## Public API

### Functions

#### `check_safety`
```python
def check_safety(
    text: str,
    safety_checkers: List[Callable],
    text_type: str
) -> Tuple[bool, str]
```

Run text through all safety checkers and return combined result.

**Parameters:**
- `text` - Content to check
- `safety_checkers` - List of checker callables (e.g., `SalesforceSafetyChecker`)
- `text_type` - Description for logging ("prompt" or "output")

**Returns:**
- `(True, "")` if all checkers pass
- `(False, message)` if any checker fails

**Contracts:**
- REQUIRES: Each checker is callable with signature `(text) -> (name, is_safe, report)`
- ENSURES: Returns immediately on first unsafe result
- ENSURES: Logs checker results with text_type
- ENSURES: Constructs user-friendly message if unsafe

**Checker Protocol:**
```python
def checker(text: str) -> Tuple[str, bool, str]:
    """
    Returns:
        name: str - Checker name for logging
        is_safe: bool - True if content is safe
        report: str - Details if unsafe (empty if safe)
    """
```

**Unsafe Message Format:**
```
"Your {context} was found to be unsafe by the {checker_name} safety checker."
```

## Usage Pattern

```python
from src.a2rchi.models.safety import SalesforceSafetyChecker
from src.a2rchi.pipelines.classic_pipelines.utils.safety_checker import check_safety

checkers = [SalesforceSafetyChecker()]

# Check prompt before sending to model
is_safe, msg = check_safety(user_prompt, checkers, "prompt")
if not is_safe:
    return msg

# Generate response
response = llm.generate(user_prompt)

# Check output before returning to user
is_safe, msg = check_safety(response, checkers, "output")
if not is_safe:
    return msg

return response
```

## Integration

Used by model classes that support safety checking:
- `HuggingFaceOpenLLM` (when `enable_salesforce_content_safety=True`)
- `LlamaLLM` (when `enable_salesforce_content_safety=True`)
- `VLLM` (when `enable_salesforce_content_safety=True`)

## Invariants

1. Empty checker list always returns `(True, "")`
2. Checks stop at first failure (short-circuit)
3. Context string is used only for logging/messaging
4. Report from checker is logged but not returned to user
