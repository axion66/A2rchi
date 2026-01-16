---
type: spec
module: a2rchi.models.llama
version: "1.0"
status: extracted
test_file: tests/unit/test_models_llama.py
source_files:
  - src/a2rchi/models/llama.py
---

# Llama Model Spec

## Overview

Custom LLM implementation for Meta's Llama models using HuggingFace transformers. Supports PEFT adapters and Salesforce safety checking.

## Dependencies

- `src/a2rchi/models/base.BaseCustomLLM` - Abstract base class
- `src/a2rchi/models/safety.SalesforceSafetyChecker` - Content safety
- `src/a2rchi/pipelines/classic_pipelines/utils.safety_checker.check_safety` - Safety wrapper
- `transformers.LlamaForCausalLM` - Llama model class
- `transformers.LlamaTokenizer` - Llama tokenizer
- `torch` - PyTorch
- `peft` (optional) - Parameter-efficient fine-tuning

## Public API

### Classes

#### `LlamaLLM`
```python
class LlamaLLM(BaseCustomLLM):
    """Loading the Llama LLM from Meta."""
    
    # Model paths
    base_model: str = None           # e.g., "meta-llama/Llama-2-70b"
    peft_model: str = None           # Optional PEFT adapter location
    
    # Safety
    enable_salesforce_content_safety: bool = True
    
    # Model loading
    quantization: bool = True
    
    # Generation parameters
    max_new_tokens: int = 2048
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
    
    # Runtime state
    tokenizer: Callable = None
    llama_model: Callable = None
    safety_checkers: List = None
```

**Constructor Behavior:**
1. Sets all kwargs as instance attributes
2. Sets random seeds if provided (both CPU and CUDA)
3. Loads `LlamaTokenizer` from `base_model`
4. Loads `LlamaForCausalLM` with float16 and device_map="auto"
5. If `peft_model` provided, wraps with `PeftModel`
6. Sets model to eval mode
7. Initializes `SalesforceSafetyChecker` if enabled

**Contracts:**
- REQUIRES: `base_model` is a valid Llama model path/ID
- REQUIRES: Model weights must be accessible (local or HuggingFace)
- ENSURES: Model loaded to GPU with automatic device mapping
- ENSURES: Model in eval mode

**Properties:**
- `_llm_type` → `"custom"`

##### `_call`
```python
def _call(self, prompt: str = None, stop: Optional[List[str]] = None) -> str
```

Generate response from Llama model.

**Contracts:**
- REQUIRES: `prompt` is non-empty string
- ENSURES: Runs safety check on prompt (returns safety message if unsafe)
- ENSURES: Wraps prompt in `[INST]...[/INST]` format
- ENSURES: Runs safety check on output (returns safety message if unsafe)
- ENSURES: Returns text after `[/INST]` marker (strips prompt)

**Processing Steps:**
1. Safety check prompt → return early if unsafe
2. Tokenize: `"[INST]" + prompt + "[/INST]"`
3. Move tensors to CUDA
4. Generate with configured parameters
5. Decode output
6. Safety check output → return safety message if unsafe
7. Extract text after `[/INST]` marker

## Prompt Format

Uses Llama 2 instruction format:
```
[INST]<user prompt>[/INST]<model response>
```

## Invariants

1. Always uses float16 precision
2. Safety checking is enabled by default
3. Model loaded with `safetensors=True`
4. Does NOT use model caching (unlike HuggingFaceOpenLLM)

## Notes

- This class is specifically for Llama models
- For other HuggingFace models, use `HuggingFaceOpenLLM`
- Quantization parameter exists but is not implemented (always uses float16)
