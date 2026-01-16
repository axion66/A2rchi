# Uplift Models Module

## Overview

Extract G5 specs from the models module (`src/a2rchi/models/`). This module provides LLM adapters for various providers (OpenAI, Anthropic, Ollama, HuggingFace, vLLM).

## Goals

1. Extract specs for all 11 model classes
2. Document the inheritance hierarchy (BaseCustomLLM → specific implementations)
3. Document the caching mechanism for model instances
4. Enable G5 workflow for future model additions

## Non-Goals

- Refactoring existing code
- Adding new model providers
- Changing existing behavior

## Module Structure

```
src/a2rchi/models/
├── __init__.py          # Exports all model classes
├── base.py              # BaseCustomLLM abstract class
├── anthropic.py         # AnthropicLLM (langchain wrapper)
├── claude.py            # ClaudeLLM (direct API)
├── dumb.py              # DumbLLM (testing/mock)
├── huggingface_image.py # HuggingFaceImageLLM
├── huggingface_open.py  # HuggingFaceOpenLLM
├── llama.py             # LlamaLLM
├── ollama.py            # OllamaInterface (langchain wrapper)
├── openai.py            # OpenAILLM (langchain wrapper)
├── safety.py            # SalesforceSafetyChecker
└── vllm.py              # VLLM
```

## Architecture

### Inheritance Hierarchy

1. **LangChain Wrappers** (extend existing LangChain classes):
   - `OpenAILLM` → `ChatOpenAI`
   - `AnthropicLLM` → `ChatAnthropic`
   - `OllamaInterface` → `ChatOllama`

2. **Custom Implementations** (extend BaseCustomLLM):
   - `ClaudeLLM` → `BaseCustomLLM` (direct Anthropic API)
   - `HuggingFaceOpenLLM` → `BaseCustomLLM` (transformers)
   - `HuggingFaceImageLLM` → `BaseCustomLLM` (transformers)
   - `LlamaLLM` → `BaseCustomLLM` (llama-cpp-python)
   - `VLLM` → `BaseCustomLLM` (vLLM engine)
   - `DumbLLM` → `BaseCustomLLM` (mock/testing)

3. **Utility Classes**:
   - `SalesforceSafetyChecker` - Content safety checking

### Caching

BaseCustomLLM implements `_MODEL_CACHE` class variable for caching expensive model loads:
- `get_cached_model(key)` - Retrieve cached model
- `set_cached_model(key, value)` - Store model in cache

## Specs to Create

| Spec | Class(es) | Type |
|------|-----------|------|
| `models/base.spec.md` | `BaseCustomLLM`, `print_model_params` | Abstract base |
| `models/langchain-wrappers.spec.md` | `OpenAILLM`, `AnthropicLLM`, `OllamaInterface` | Thin wrappers |
| `models/claude.spec.md` | `ClaudeLLM` | Direct API |
| `models/huggingface.spec.md` | `HuggingFaceOpenLLM`, `HuggingFaceImageLLM` | Local models |
| `models/llama.spec.md` | `LlamaLLM` | llama-cpp |
| `models/vllm.spec.md` | `VLLM` | vLLM engine |
| `models/safety.spec.md` | `SalesforceSafetyChecker` | Content safety |
| `models/dumb.spec.md` | `DumbLLM` | Mock/testing |

## Success Criteria

- [ ] All model classes have specs
- [ ] Inheritance relationships documented
- [ ] Caching mechanism specified
- [ ] Safety checker integration documented
