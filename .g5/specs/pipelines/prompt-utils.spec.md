---
type: spec
module: a2rchi.pipelines.classic_pipelines.utils.prompts
version: "1.0"
status: extracted
test_file: tests/unit/test_prompt_utils.py
source_files:
  - src/a2rchi/pipelines/classic_pipelines/utils/prompt_formatters.py
  - src/a2rchi/pipelines/classic_pipelines/utils/prompt_validator.py
  - src/a2rchi/pipelines/classic_pipelines/utils/prompt_utils.py
---

# Prompt Utilities Spec

## Overview

Prompt handling utilities including file loading, validation, and model-specific formatting. Supports instructor templates, chat templates, and base templates.

## Dependencies

- `src/a2rchi/pipelines/classic_pipelines/utils/history_utils`
- `langchain_core.prompts.PromptTemplate`

## Public API

### Functions

#### `read_prompt`
```python
def read_prompt(path: str) -> str
```
Read prompt template from file.

**Contracts:**
- REQUIRES: `path` is a valid file path
- ENSURES: Returns file contents as string
- ENSURES: Raises `FileNotFoundError` if file doesn't exist

---

### Classes

#### `ValidatedPromptTemplate`
```python
class ValidatedPromptTemplate(PromptTemplate):
    """PromptTemplate with input variable validation."""
    
    name: str
```

**Constructor:**
```python
def __init__(self, name: str, prompt_template: str)
```

**Contracts:**
- REQUIRES: `name` is a string identifier
- REQUIRES: `prompt_template` is the template text
- ENSURES: Validates variables against `SUPPORTED_INPUT_VARIABLES`
- ENSURES: Logs warning for unsupported variables

**Supported Variables:**
```python
SUPPORTED_INPUT_VARIABLES = [
    'question', 'history', 'documents', 'context',
    'submission_text', 'rubric_text', 'summary',
    'analysis', 'additional_comments', 'condense_output',
    'retriever_output', 'condensed_question', ...
]
```

---

#### `PromptFormatter`
```python
class PromptFormatter:
    """Format prompts for specific model architectures."""
    
    tokenizer: Any
    special_tokens: Dict
    apply_format: Callable
    strip_html: bool
    tag_roles: Dict[str, str]
```

**Constructor:**
```python
def __init__(self, tokenizer, strip_html: bool = False)
```

**Contracts:**
- REQUIRES: `tokenizer` has `special_tokens_map` attribute
- ENSURES: Detects template type from special tokens
- ENSURES: Sets `apply_format` to appropriate formatter

**Methods:**

##### `format_prompt`
```python
def format_prompt(self, prompt: str) -> Tuple[str, str]
```
Main formatting function.

**Contracts:**
- ENSURES: Strips tags from prompt
- ENSURES: Optionally strips HTML if `strip_html=True`
- ENSURES: Applies detected template format
- ENSURES: Returns `(formatted_prompt, end_tag)`

##### `_strip_tags`
```python
def _strip_tags(self, text: str) -> str
```
Remove `<tag>` and `</tag>` markers.

##### `_strip_html`
```python
def _strip_html(self, text: str) -> str
```
Remove HTML tags and unescape entities.

##### `_get_formatter`
```python
def _get_formatter(self) -> Callable
```
Select formatter based on tokenizer's special tokens.

**Detection Logic:**
1. If `[INST]` in special tokens → `_apply_instructor_template`
2. If `<|im_start|>` in special tokens → `_apply_chat_template`
3. Else → `_apply_base_template`

##### `_apply_instructor_template`
```python
def _apply_instructor_template(self, prompt: str) -> Tuple[str, str]
```
Format for Llama-style instruction models.

**Returns:** `(f"[INST] {prompt} [/INST]", "[/INST]")`

##### `_apply_chat_template`
```python
def _apply_chat_template(self, prompt: str) -> Tuple[str, str]
```
Format for chat models (Qwen, etc.).

**Contracts:**
- ENSURES: Parses prompt into message list via `_tuplize_tagged_prompt`
- ENSURES: Calls `tokenizer.apply_chat_template()`
- ENSURES: Returns `(formatted, "assistant")`

##### `_tuplize_tagged_prompt`
```python
def _tuplize_tagged_prompt(self, text: str) -> List[Dict]
```
Parse tagged prompt into message list.

**Contracts:**
- ENSURES: Extracts `<tag>content</tag>` blocks
- ENSURES: Maps tags to roles via `tag_roles`
- ENSURES: Expands `<history>` into individual messages
- ENSURES: Returns list of `{"role": ..., "content": ...}` dicts

**Tag Roles:**
```python
tag_roles = {
    "question": "user",
    "documents": "assistant",
    "condensed_question": "user"
}
```

## Template Types

| Type | Detection | Format |
|------|-----------|--------|
| Instructor | `[INST]` token | `[INST] prompt [/INST]` |
| Chat | `<\|im_start\|>` token | `apply_chat_template()` |
| Base | (default) | No modification |

## Invariants

1. Tags are always stripped before formatting
2. HTML stripping is optional (off by default)
3. Unknown tags in prompts are left as-is
4. History tag content is expanded into multiple messages
