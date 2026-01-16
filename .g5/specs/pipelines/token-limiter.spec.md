---
type: spec
module: a2rchi.pipelines.classic_pipelines.utils.token_limiter
version: "1.0"
status: extracted
test_file: tests/unit/test_token_limiter.py
source_files:
  - src/a2rchi/pipelines/classic_pipelines/utils/token_limiter.py
---

# Token Limiter Spec

## Overview

Manages LLM context window limits by intelligently pruning history, documents, and other inputs. Ensures prompts stay within model token limits while preserving essential content.

## Dependencies

- `src/a2rchi/pipelines/classic_pipelines/utils/history_utils`
- `langchain_core.documents.Document`
- `langchain_core.language_models.base.BaseLanguageModel`
- `langchain_core.prompts.base.BasePromptTemplate`

## Public API

### Classes

#### `TokenLimiter`
```python
class TokenLimiter:
    """Manages token limits for LLM inputs."""
    
    # Configuration
    llm: BaseLanguageModel
    max_tokens: int
    effective_max_tokens: int
    reserved_tokens: int
    prompt_tokens: int
    min_history_messages: int = 2
    min_docs: int = 0
    large_msg_threshold: int
    unprunable_input_variables: List[str]
    
    INPUT_SIZE_WARNING: str = "WARNING: your last message is too large..."
```

**Constructor:**
```python
def __init__(
    self,
    llm: BaseLanguageModel,
    max_tokens: int = 1e10,
    prompt: BasePromptTemplate = None,
    reserved_tokens: int = 0,
    min_history_messages: int = 2,
    min_docs: int = 0,
    large_msg_fraction: float = 0.5,
    unprunable_input_variables: List[str] = ["question"]
)
```

**Contracts:**
- ENSURES: Calculates `prompt_tokens` from empty prompt
- ENSURES: `effective_max_tokens = max_tokens - reserved_tokens - prompt_tokens`
- ENSURES: `large_msg_threshold = effective_max_tokens * large_msg_fraction`

**Methods:**

##### `calculate_effective_max_tokens`
```python
def calculate_effective_max_tokens(self) -> int
```
Calculate usable token budget.

**Contracts:**
- ENSURES: Returns `max_tokens - reserved_tokens - prompt_tokens`
- ENSURES: Logs warning if result < 100
- ENSURES: Returns 1000 as fallback if result <= 0

##### `get_max_tokens`
```python
def get_max_tokens(self, max_tokens: int = 1e10) -> int
```
Get effective max tokens from config and LLM.

**Contracts:**
- ENSURES: Returns minimum of user config and LLM's `max_tokens` attribute

##### `safe_token_count`
```python
def safe_token_count(self, text: str) -> int
```
Safely count tokens in text.

**Contracts:**
- ENSURES: Handles None input (uses empty string)
- ENSURES: Converts non-strings to string
- ENSURES: Falls back to `len(text) // 4` if `get_num_tokens` fails

##### `check_input_size`
```python
def check_input_size(self, text: str) -> bool
```
Check if input fits within limits.

**Contracts:**
- ENSURES: Returns `True` if text tokens <= effective_max_tokens

##### `prune_inputs_to_token_limit`
```python
def prune_inputs_to_token_limit(
    self,
    question: str = "",
    history: List[Tuple[str, str]] | str = [],
    **kwargs: Any
) -> Dict[str, Any]
```
Reduce inputs to fit token limit.

**Contracts:**
- ENSURES: Never removes `question` or `unprunable_input_variables`
- ENSURES: Prunes in priority order (see below)
- ENSURES: Returns dict with pruned inputs

**Pruning Priority:**
```
1a. Remove very large history messages (> large_msg_threshold)
1b. Remove old history messages (keep min_history_messages)
2. Remove last documents from each document list
3. Remove extra string variables
```

## Token Calculation

```
effective_max = max_tokens - reserved_tokens - prompt_tokens

For each input:
  - question_tokens = count(question)
  - history_tokens = [count(msg) for msg in history]
  - doc_tokens = [[count(d.page_content) for d in docs] for docs in doc_lists]
  - extra_tokens = {k: count(v) for k, v in extras}

Total = question_tokens + sum(history_tokens) + sum(doc_tokens) + sum(extra_tokens)
```

## Document Detection

Documents are identified by checking if input value is:
1. A list or tuple
2. First element has `page_content` attribute (LangChain Document)

## Invariants

1. Question is never pruned
2. Unprunable variables are never pruned (but may trigger warning)
3. History string inputs are converted to tuple format for pruning
4. Large messages are removed before old messages
5. Documents are removed round-robin from multiple lists
