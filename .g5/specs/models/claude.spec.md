---
type: spec
module: a2rchi.models.claude
version: "1.0"
status: extracted
test_file: tests/unit/test_models_claude.py
source_files:
  - src/a2rchi/models/claude.py
---

# Claude Direct API Spec

## Overview

Custom LLM implementation that calls Anthropic's Claude API directly via HTTP, bypassing LangChain's wrapper. Useful when more control over the API call is needed.

## Dependencies

- `src/a2rchi/models/base.BaseCustomLLM` - Abstract base class
- `src/utils/logging` - Logging utilities
- `requests` - HTTP client

## Public API

### Classes

#### `ClaudeLLM`
```python
class ClaudeLLM(BaseCustomLLM):
    """An LLM class that uses Anthropic's Claude model via direct API."""
    
    api_key: str = "INSERT KEY HERE!!!"
    base_url: str = "https://api.anthropic.com/v1/messages"
    model_name: str = "claude-3-5-sonnet-20240620"
    verbose: bool = False
```

**Methods:**

##### `_call`
```python
def _call(
    self,
    prompt: str = None,
    stop: Optional[List[str]] = None,
    max_tokens: int = 1024,
) -> str
```

Send prompt to Claude API and return response.

**Contracts:**
- REQUIRES: `self.api_key` is a valid Anthropic API key
- REQUIRES: `prompt` is a non-empty string
- ENSURES: Returns content from Claude's response
- ENSURES: If `stop` is provided, logs warning (not supported)
- ENSURES: If `verbose=True`, logs request/response details

**API Request Format:**
```json
{
  "model": "<model_name>",
  "max_tokens": 1024,
  "messages": [
    {"role": "user", "content": "<prompt>"}
  ]
}
```

**Headers:**
```
x-api-key: <api_key>
anthropic-version: 2023-06-01
Content-Type: application/json
```

**Response Handling:**
- Extracts `response.json()["content"][0]["text"]`
- Raises on HTTP errors

## Invariants

1. Uses Anthropic's messages API (v1/messages endpoint)
2. Always sends single-turn conversations (one user message)
3. Stop tokens are logged but not implemented

## Error Handling

- HTTP errors propagate as `requests.exceptions.HTTPError`
- Invalid API key returns 401 Unauthorized
- Rate limiting returns 429 Too Many Requests

## Usage Pattern

```python
llm = ClaudeLLM(api_key="sk-ant-...", model_name="claude-3-5-sonnet-20240620")
response = llm._call("What is 2+2?")
# Or via LangChain interface:
response = llm.invoke("What is 2+2?")
```

## Notes

- Prefer `AnthropicLLM` (LangChain wrapper) for standard usage
- Use this class when you need direct control over API parameters
- The default `api_key` value is a placeholder - must be overridden
