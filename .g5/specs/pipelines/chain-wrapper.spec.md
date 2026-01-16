---
type: spec
module: a2rchi.pipelines.classic_pipelines.utils.chain_wrappers
version: "1.0"
status: extracted
test_file: tests/unit/test_chain_wrappers.py
source_files:
  - src/a2rchi/pipelines/classic_pipelines/utils/chain_wrappers.py
---

# Chain Wrapper Spec

## Overview

Generic wrapper around LangChain chains that provides token limiting, input validation, and harmonized interface for A2rchi pipelines.

## Dependencies

- `src/a2rchi/pipelines/classic_pipelines/utils/token_limiter.TokenLimiter`
- `src/utils/config_loader.load_global_config`
- `langchain_core.language_models.base.BaseLanguageModel`
- `langchain_core.prompts.base.BasePromptTemplate`

## Public API

### Classes

#### `ChainWrapper`
```python
class ChainWrapper:
    """Generic wrapper around LangChain chains with token limiting."""
    
    chain: Any                              # Underlying LangChain chain
    llm: BaseLanguageModel                  # Language model
    prompt: BasePromptTemplate              # Prompt template
    required_input_variables: List[str]     # Must be in prompt
    unprunable_input_variables: List[str]   # Cannot be truncated
    token_limiter: TokenLimiter             # Token management
```

**Constructor:**
```python
def __init__(
    self,
    chain: Any,
    llm: BaseLanguageModel,
    prompt: BasePromptTemplate,
    required_input_variables: List[str] = ['question'],
    unprunable_input_variables: Optional[List[str]] = [],
    max_tokens: int = 1e10
)
```

**Contracts:**
- REQUIRES: All `required_input_variables` exist in `prompt.input_variables`
- ENSURES: `TokenLimiter` initialized with LLM and prompt
- ENSURES: Raises `ValueError` if required variable missing from prompt

**Methods:**

##### `_check_prompt` (protected)
```python
def _check_prompt(self, prompt: BasePromptTemplate) -> BasePromptTemplate
```
Validate prompt contains required variables.

**Contracts:**
- REQUIRES: `prompt` is a valid LangChain prompt template
- ENSURES: Returns prompt if valid
- ENSURES: Raises `ValueError` if missing required variable

##### `_prepare_payload` (protected)
```python
def _prepare_payload(self, inputs: Dict[str, Any]) -> Dict[str, Any]
```
Prepare inputs for chain invocation.

**Contracts:**
- ENSURES: Calls `token_limiter.prune_inputs_to_token_limit(**inputs)`
- ENSURES: Initializes missing prompt variables to empty string
- ENSURES: Logs debug info for missing variables

##### `invoke`
```python
def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]
```
Execute the chain with input validation and token limiting.

**Contracts:**
- REQUIRES: `inputs` is a dict of input variables
- ENSURES: Checks unprunable variables aren't too large
- ENSURES: Returns early with warning if unprunable too large
- ENSURES: Prepares payload via `_prepare_payload`
- ENSURES: Calls underlying `chain.invoke()`
- ENSURES: Returns `{"answer": ..., **input_variables}`

**Return Value:**
```python
{
    "answer": "<chain output>",
    # Plus all input variables used
}
```

## Token Limiting Integration

The `ChainWrapper` delegates token management to `TokenLimiter`:

1. **Unprunable check**: If `unprunable_input_variables` exceed limits, return warning
2. **Pruning**: History and documents are truncated to fit token budget
3. **Defaults**: Missing prompt variables initialized to empty string

## Error Handling

- Missing required prompt variable: `ValueError` at construction
- Unprunable variable too large: Returns `INPUT_SIZE_WARNING` message
- Missing optional input: Initialized to empty string (with warning)

## Usage Pattern

```python
wrapper = ChainWrapper(
    chain=prompt | llm | StrOutputParser(),
    llm=my_llm,
    prompt=my_prompt,
    required_input_variables=['question'],
    unprunable_input_variables=['question'],
    max_tokens=7000,
)

result = wrapper.invoke({"question": "What is AI?", "history": [...]})
print(result["answer"])
```
