---
type: spec
module: a2rchi.models.huggingface
version: "1.0"
status: extracted
test_file: tests/unit/test_models_huggingface.py
source_files:
  - src/a2rchi/models/huggingface_open.py
  - src/a2rchi/models/huggingface_image.py
---

# HuggingFace Models Spec

## Overview

Custom LLM implementations for loading open-source models from HuggingFace Hub. Supports text-only and vision-language models with optional quantization and safety checking.

## Dependencies

- `src/a2rchi/models/base.BaseCustomLLM` - Abstract base class
- `src/a2rchi/models/safety.SalesforceSafetyChecker` - Content safety
- `src/a2rchi/pipelines/classic_pipelines/utils.prompt_formatters.PromptFormatter` - Prompt formatting
- `src/a2rchi/pipelines/classic_pipelines/utils.safety_checker.check_safety` - Safety check wrapper
- `transformers` - HuggingFace transformers library
- `torch` - PyTorch

## Public API

### Classes

#### `HuggingFaceOpenLLM`
```python
class HuggingFaceOpenLLM(BaseCustomLLM):
    """Loading any chat-based LLM available on HuggingFace."""
    
    # Model configuration
    base_model: str = None           # HF model ID (e.g., "meta-llama/Llama-2-70b")
    peft_model: str = None           # Optional PEFT adapter path
    quantization: bool = False       # Enable 8-bit quantization
    enable_salesforce_content_safety: bool = False
    
    # Generation parameters
    max_new_tokens: int = 1024
    seed: int = None
    do_sample: bool = True
    min_length: int = None
    use_cache: bool = True
    top_p: float = 0.9
    temperature: float = 0.6
    top_k: int = 50
    repetition_penalty: float = 1.0
    length_penalty: int = 1
    max_padding_length: int = None
    
    # Runtime state (set in __init__)
    tokenizer: Callable = None
    formatter: Callable = None
    hf_model: Callable = None
    safety_checkers: List = None
```

**Constructor Behavior:**
1. Sets all kwargs as instance attributes
2. Loads tokenizer from `base_model`
3. Checks model cache for existing model
4. If not cached: loads model (with optional quantization/PEFT)
5. Caches model with key `(base_model, quantization, peft_model)`
6. Sets up `PromptFormatter` for the tokenizer
7. Optionally initializes `SalesforceSafetyChecker`

**Contracts:**
- REQUIRES: `base_model` is a valid HuggingFace model ID
- REQUIRES: If `peft_model` specified, PEFT library must be installed
- REQUIRES: If `quantization=True`, BitsAndBytes must be installed
- ENSURES: Model is loaded to GPU with `device_map="auto"`
- ENSURES: Model is in eval mode after loading

##### `_call`
```python
def _call(self, prompt: str = None, stop: Optional[List[str]] = None) -> str
```

**Contracts:**
- REQUIRES: `prompt` is non-empty string
- ENSURES: Runs safety check on prompt if `enable_salesforce_content_safety=True`
- ENSURES: Formats prompt using `formatter.format_prompt()`
- ENSURES: Returns generated text with prompt stripped
- ENSURES: Runs safety check on output if enabled

---

#### `HuggingFaceImageLLM`
```python
class HuggingFaceImageLLM(BaseCustomLLM):
    """Loading image-based LLMs (Vision-Language models) from HuggingFace."""
    
    # Model configuration
    base_model: str = None
    quantization: bool = False
    
    # Image processing
    min_pixels: int = 224 * 28 * 28
    max_pixels: int = 1280 * 28 * 28
    
    # Generation parameters
    max_new_tokens: int = 1024
    seed: int = None
    do_sample: bool = False
    min_length: int = None
    use_cache: bool = True
    top_k: int = 50
    repetition_penalty: float = 1.0
    length_penalty: int = 1
    
    # Runtime state
    processor: Callable = None
    hf_model: Callable = None
```

**Constructor Behavior:**
1. Loads `AutoProcessor` with pixel constraints
2. Loads `Qwen2_5_VLForConditionalGeneration` model
3. Caches model with key `(base_model, quantization, None)`

##### `_call`
```python
def _call(
    self,
    prompt: Union[str, List[Dict[str, Any]]] = None,
    stop: Optional[List[str]] = None,
) -> str
```

**Contracts:**
- REQUIRES: `prompt` can be string or list of message dicts with images
- ENSURES: Processes vision info using `qwen_vl_utils.process_vision_info`
- ENSURES: Returns generated text

## Caching Strategy

Both classes use `BaseCustomLLM._MODEL_CACHE` with tuple keys:
```python
key = (base_model, quantization, peft_model)
```

This prevents reloading expensive models when creating multiple instances.

## Invariants

1. Models are always loaded to GPU (`device_map="auto"`)
2. Models use `torch.float16` for memory efficiency
3. Models are always in eval mode (no gradient computation)
4. Cache is stored at `/root/models/` (hardcoded)

## Safety Checking

When `enable_salesforce_content_safety=True`:
1. Prompt is checked before generation
2. Output is checked after generation
3. Unsafe content returns safety message instead of model output
