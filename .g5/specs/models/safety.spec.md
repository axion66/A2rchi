---
type: spec
module: a2rchi.models.safety
version: "1.0"
status: extracted
test_file: tests/unit/test_models_safety.py
source_files:
  - src/a2rchi/models/safety.py
---

# Safety Checker Spec

## Overview

Content safety checking using Salesforce's safety-flan-t5-base model. Detects unsafe content across multiple categories including toxicity, hate, violence, and profanity.

## Dependencies

- `transformers.AutoConfig` - Model configuration
- `transformers.AutoModelForSeq2SeqLM` - Seq2Seq model
- `transformers.AutoTokenizer` - Tokenizer
- `torch` - PyTorch
- `src/utils/logging` - Logging utilities

## Public API

### Classes

#### `SalesforceSafetyChecker`
```python
class SalesforceSafetyChecker:
    """Content safety checker using Salesforce's safety-flan-t5-base model."""
```

**Constructor:**
```python
def __init__(self):
    # Loads model and tokenizer from "Salesforce/safety-flan-t5-base"
    # Sets model to eval mode
```

**Contracts:**
- ENSURES: Model loaded from HuggingFace Hub
- ENSURES: Model in eval mode (no gradients)

##### `__call__`
```python
def __call__(self, output_text: str) -> Tuple[str, bool, str]
```

Check if text content is safe.

**Parameters:**
- `output_text` - Text to check for safety

**Returns:**
Tuple of:
1. `str` - Model name ("Salesforce Content Safety Flan T5 Base")
2. `bool` - `True` if safe, `False` if unsafe
3. `str` - Report with category scores (empty if safe)

**Contracts:**
- REQUIRES: `output_text` is a string
- ENSURES: Returns tuple of (model_name, is_safe, report)
- ENSURES: Logs warning if input > 512 tokens
- ENSURES: If unsafe, report contains scores for all categories

**Safety Categories:**
| Category | Description |
|----------|-------------|
| toxicity | Toxic language |
| hate | Hate speech |
| identity | Identity-based attacks |
| violence | Violent content |
| physical | Physical harm |
| sexual | Sexual content |
| profanity | Profane language |
| biased | Biased content |

**Report Format (when unsafe):**
```
| toxicity | hate | identity | violence | physical | sexual | profanity | biased |
|  0.123   | 0.45 |   0.01   |   0.02   |   0.01   |  0.01  |   0.89    |  0.02  |
```

## Implementation Details

**Prompt Format:**
```
Is the <Text> field safe or unsafe? <Text> {output_text} <Context> 
```

**Detection Logic:**
1. Tokenize prompt with prefix
2. Generate classification output
3. Check if first word is "safe"
4. If unsafe, extract softmax scores for each category

**Score Extraction:**
- Uses output logits at specific positions (3, 5, 7, 9, 11, 13, 15, 17)
- Computes softmax over "true"/"false" token IDs
- Reports probability of "true" (unsafe) for each category

## Invariants

1. Model is always in eval mode
2. Uses greedy decoding (no sampling)
3. Max new tokens: 20
4. Input truncation warning at 512 tokens

## Usage Pattern

```python
checker = SalesforceSafetyChecker()
model_name, is_safe, report = checker("Some text to check")
if not is_safe:
    print(f"Unsafe content detected:\n{report}")
```

## Integration

Used by other models when `enable_salesforce_content_safety=True`:
- `HuggingFaceOpenLLM`
- `LlamaLLM`
- `VLLM`

Checking is done via `check_safety()` wrapper function in pipelines.
