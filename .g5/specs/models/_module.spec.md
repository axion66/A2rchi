---
spec_id: a2rchi/models
type: module
status: extracted
children:
  - a2rchi/models/base
  - a2rchi/models/langchain-wrappers
  - a2rchi/models/claude
  - a2rchi/models/huggingface
  - a2rchi/models/llama
  - a2rchi/models/vllm
  - a2rchi/models/safety
  - a2rchi/models/dumb
---

# Models Module

LLM implementations for A2rchi. All models implement a common interface for text generation.

## Exports

```python
from src.a2rchi.models import (
    BaseCustomLLM,      # Abstract base class
    OpenAILLM,          # OpenAI GPT models
    AnthropicLLM,       # Anthropic Claude (LangChain)
    ClaudeLLM,          # Anthropic Claude (direct API)
    HuggingFaceOpenLLM, # HuggingFace text models
    HuggingFaceImageLLM,# HuggingFace vision models
    LlamaLLM,           # Llama models
    VLLM,               # vLLM inference engine
    OllamaInterface,    # Ollama local models
    DumbLLM,            # Testing stub
    SalesforceSafetyChecker,
    print_model_params,
)
```

## Class Hierarchy

```
LLM (LangChain)
├── ChatOpenAI
│   └── OpenAILLM
├── ChatAnthropic
│   └── AnthropicLLM
├── ChatOllama
│   └── OllamaInterface
└── BaseCustomLLM (custom base)
    ├── ClaudeLLM
    ├── HuggingFaceOpenLLM
    ├── HuggingFaceImageLLM
    ├── LlamaLLM
    ├── VLLM
    └── DumbLLM
```

## Model Caching

All `BaseCustomLLM` subclasses use class-level caching:

```python
class SomeModel(BaseCustomLLM):
    _MODEL_CACHE = {}  # Defined at module level after class
```

Cache key format: `(base_model, quantization, peft_model)`

## Common Interface

All models support:
- `invoke(prompt)` → Response text
- `_call(prompt, stop)` → Internal generation
- `_llm_type` property → Model identifier

## Dependencies

- `langchain_openai`, `langchain_anthropic`, `langchain_ollama`
- `transformers`, `torch` (for HuggingFace models)
- `vllm` (for VLLM)
- `anthropic` (for ClaudeLLM direct API)
