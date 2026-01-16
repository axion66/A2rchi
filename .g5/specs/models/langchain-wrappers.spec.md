---
type: spec
module: a2rchi.models.langchain_wrappers
version: "1.0"
status: extracted
test_file: tests/unit/test_models_langchain.py
source_files:
  - src/a2rchi/models/openai.py
  - src/a2rchi/models/anthropic.py
  - src/a2rchi/models/ollama.py
---

# LangChain Wrapper Models Spec

## Overview

Thin wrapper classes around LangChain's official model integrations. These provide consistent defaults and interface for A2rchi's model loading system.

## Dependencies

- `langchain_openai.ChatOpenAI` - OpenAI chat models
- `langchain_anthropic.ChatAnthropic` - Anthropic Claude models
- `langchain_ollama.chat_models.ChatOllama` - Ollama local models
- `src/utils/logging` - Logging utilities

## Public API

### Classes

#### `OpenAILLM`
```python
class OpenAILLM(ChatOpenAI):
    """Loading the various OpenAI models (gpt-4, gpt-3.5-turbo)."""
    
    model_name: str = "gpt-4"
    temperature: int = 1
```

**Contracts:**
- REQUIRES: `OPENAI_API_KEY` environment variable is set
- ENSURES: Inherits all `ChatOpenAI` functionality

**Usage:**
```python
llm = OpenAILLM(model_name="gpt-4", temperature=0.7)
response = llm.invoke("Hello")
```

---

#### `AnthropicLLM`
```python
class AnthropicLLM(ChatAnthropic):
    """Loading Anthropic model from langchain package."""
    
    model_name: str = "claude-3-opus-20240229"
    temp: int = 1
```

**Contracts:**
- REQUIRES: `ANTHROPIC_API_KEY` environment variable is set
- ENSURES: Inherits all `ChatAnthropic` functionality

**Supported Models:**
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`

---

#### `OllamaInterface`
```python
class OllamaInterface(ChatOllama):
    """LLM class using a model connected to an Ollama server."""
    
    model_name: str = ""
    url: str = ""
```

**Constructor:**
```python
def __init__(self, **kwargs):
    # Extracts 'base_model' and 'url' from kwargs
    # Logs error if url or model_name is empty
```

**Contracts:**
- REQUIRES: `url` is provided and non-empty (logs error otherwise)
- REQUIRES: `base_model` is provided and non-empty (logs error otherwise)
- ENSURES: Initializes parent `ChatOllama` with `model=base_model`, `base_url=url`

**Usage:**
```python
llm = OllamaInterface(base_model="llama2", url="http://localhost:11434")
response = llm.invoke("Hello")
```

## Invariants

1. All wrappers delegate to parent LangChain class for actual API calls
2. API keys must be set as environment variables (not passed directly)
3. All classes are compatible with LangChain's chat model interface

## Notes

- These are the simplest model integrations - just configuration wrappers
- For custom API handling, see `ClaudeLLM` which calls Anthropic API directly
