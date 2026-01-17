---
type: spec
module: a2rchi.models.vllm
version: "1.0"
status: extracted
test_file: tests/unit/test_models_vllm.py
source_files:
  - src/a2rchi/models/vllm.py
---

# vLLM Model Spec

## Overview

Custom LLM implementation using the vLLM inference engine for high-performance model serving. Supports tensor parallelism for multi-GPU deployment.

## Dependencies

- `src/a2rchi/models/base.BaseCustomLLM` - Abstract base class
- `src/a2rchi/models/safety.SalesforceSafetyChecker` - Content safety
- `src/a2rchi/pipelines/classic_pipelines/utils.prompt_formatters.PromptFormatter` - Prompt formatting
- `src/a2rchi/pipelines/classic_pipelines/utils.safety_checker.check_safety` - Safety wrapper
- `vllm.LLM` - vLLM inference engine
- `transformers.AutoTokenizer` - Tokenizer
- `torch` - PyTorch

## Public API

### Classes

#### `VLLM`
```python
class VLLM(BaseCustomLLM):
    """Loading a vLLM Model using the vllm Python package."""
    
    # Model configuration
    base_model: str = "Qwen/Qwen2.5-7B-Instruct-1M"
    
    # Generation parameters
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 50
    repetition_penalty: float = 1.5
    seed: int = None
    max_new_tokens: int = 2048
    length_penalty: int = 1
    
    # Safety
    enable_salesforce_content_safety: bool = False
    
    # vLLM engine configuration
    gpu_memory_utilization: float = 0.7
    tensor_parallel_size: int = 1
    trust_remote_code: bool = True
    tokenizer_mode: str = "auto"
    max_model_len: Optional[int] = None
    
    # Runtime state
    vllm_engine: object = None
    tokenizer: Callable = None
    formatter: Callable = None
    hf_model: Callable = None
    safety_checkers: List = None
```

**Constructor Behavior:**
1. Sets all kwargs as instance attributes
2. Sets environment variables for MKL and vLLM dtype
3. Loads tokenizer from `base_model`
4. Creates `PromptFormatter` with the tokenizer
5. Checks model cache for existing vLLM engine
6. If not cached: creates `vllm.LLM` engine with config
7. Caches engine with key `(base_model, "", "")`
8. Initializes safety checkers if enabled

**Environment Setup:**
```python
os.environ["MKL_THREADING_LAYER"] = "GNU"
os.environ["MKL_SERVICE_FORCE_INTEL"] = "1"
os.environ["VLLM_DEFAULT_DTYPE"] = "float16"
```

**Contracts:**
- REQUIRES: vLLM package installed (version 0.8.5 recommended)
- REQUIRES: Sufficient GPU memory for model
- ENSURES: Engine created with specified tensor parallelism
- ENSURES: Engine cached for reuse

**Properties:**
- `_llm_type` → `"custom"`

##### `_call`
```python
def _call(self, prompt: str = None, stop: Optional[List[str]] = None) -> str
```

Generate response using vLLM engine.

**Contracts:**
- REQUIRES: `prompt` is non-empty string
- ENSURES: Runs safety check on prompt if enabled
- ENSURES: Formats prompt using `formatter.format_prompt()`
- ENSURES: Calls `vllm_engine.generate()` with `SamplingParams`
- ENSURES: Runs safety check on output if enabled
- ENSURES: Returns generated text

**SamplingParams:**
```python
SamplingParams(
    temperature=self.temperature,
    top_p=self.top_p,
    top_k=self.top_k,
    max_tokens=self.max_new_tokens,
    repetition_penalty=self.repetition_penalty,
    stop=stop,
)
```

## vLLM Engine Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `gpu_memory_utilization` | 0.7 | Fraction of GPU memory to use |
| `tensor_parallel_size` | 1 | Number of GPUs for tensor parallelism |
| `tokenizer_mode` | "auto" | Tokenizer loading mode |
| `max_model_len` | None | Maximum sequence length |
| `trust_remote_code` | True | Allow custom model code |

## Caching Strategy

Uses simplified cache key: `(base_model, "", "")`
- Only caches the vLLM engine
- Tokenizer is NOT cached (always reloaded)

## Known Issues

- Older vLLM version (0.8.5) required due to XFormers bug in newer versions
- Error in newer versions: `TypeError: XFormersImpl.__init__() got an unexpected keyword argument 'layer_idx'`

## Invariants

1. Always uses float16 dtype
2. Engine is cached at class level
3. MKL environment must be configured before engine creation
