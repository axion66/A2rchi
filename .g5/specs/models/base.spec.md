---
type: spec
module: a2rchi.models.base
version: "1.0"
status: extracted
test_file: tests/unit/test_models_base.py
source_files:
  - src/a2rchi/models/base.py
---

# Base Model Spec

## Overview

Abstract base class for custom LLM implementations in A2rchi. Extends LangChain's `LLM` class and provides model caching infrastructure.

## Dependencies

- `langchain_core.language_models.llms.LLM` - Base LangChain LLM class
- `src/utils/logging` - Logging utilities

## Public API

### Functions

#### `print_model_params`
```python
def print_model_params(name: str, model_name: str, model_class_map: Dict[str, Dict[str, Any]]) -> None
```

Logs the parameters of a model instance.

**Parameters:**
- `name` - Instance name for logging
- `model_name` - Model class name (key in model_class_map)
- `model_class_map` - Mapping of model names to their classes and kwargs

**Contracts:**
- REQUIRES: `model_name` exists as key in `model_class_map`
- ENSURES: Logs formatted parameter string via logger.info

---

### Classes

#### `BaseCustomLLM`
```python
class BaseCustomLLM(LLM):
    """Abstract class used to load a custom LLM."""
    
    # Class variable for caching expensive model loads
    # NOTE: This is defined in SUBCLASSES, not in BaseCustomLLM itself.
    # Each concrete implementation (e.g., LlamaLLM) defines its own
    # _MODEL_CACHE at module level. The base class accesses it via
    # self._MODEL_CACHE which is overridden by subclasses.
    _MODEL_CACHE: ClassVar[Dict[Any, Any]] = {}  # Override in subclasses
    
    # Instance attributes
    n_tokens: int = 100
    cache: Union[BaseCache, bool, None] = None
```

**Properties:**
- `_llm_type` → `str`: Returns `"custom"`

**Class Methods:**

##### `get_cached_model`
```python
@classmethod
def get_cached_model(cls, key: Any) -> Optional[Any]
```
Retrieve a cached model by key.

**Contracts:**
- ENSURES: Returns cached value or None if not found

##### `set_cached_model`
```python
@classmethod
def set_cached_model(cls, key: Any, value: Any) -> None
```
Store a model in the class-level cache.

**Contracts:**
- ENSURES: `cls._MODEL_CACHE[key] == value`

**Abstract Methods:**

##### `_call`
```python
@abstractmethod
def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str
```
Process a prompt and return the model's response.

**Contracts:**
- REQUIRES: `prompt` is a non-empty string
- ENSURES: Returns string response from the model

## Invariants

1. `_MODEL_CACHE` is shared across all instances of a subclass
2. Cache keys should be tuples that uniquely identify a model configuration
3. All subclasses must implement `_call`

## Usage Pattern

```python
class MyLLM(BaseCustomLLM):
    def __init__(self, **kwargs):
        super().__init__()
        key = (self.model_name,)
        cached = self.get_cached_model(key)
        if cached:
            self.model = cached
        else:
            self.model = load_expensive_model()
            self.set_cached_model(key, self.model)
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        return self.model.generate(prompt)
```
