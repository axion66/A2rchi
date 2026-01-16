---
type: spec
module: a2rchi.pipelines.classic_pipelines.image
version: "1.0"
status: extracted
test_file: tests/unit/test_pipelines_image.py
source_files:
  - src/a2rchi/pipelines/classic_pipelines/image_processing.py
  - src/a2rchi/pipelines/classic_pipelines/chains.py
---

# Image Processing Pipeline Spec

## Overview

Pipeline for processing and analyzing images using vision-language models. Uses a custom `ImageLLMChain` to handle image inputs alongside text prompts.

## Dependencies

- `src/a2rchi/pipelines/classic_pipelines/base.BasePipeline`
- `src/a2rchi/pipelines/classic_pipelines/utils/chain_wrappers.ChainWrapper`
- `src/a2rchi/utils/output_dataclass.PipelineOutput`
- `langchain_classic.chains.llm.LLMChain`

## Public API

### Classes

#### `ImageLLMChain`
```python
class ImageLLMChain(LLMChain):
    """LLMChain override to pass images to custom vision LLM."""
```

##### `_call`
```python
def _call(self, inputs: Dict[str, Any]) -> Dict[str, str]
```
Process inputs with image support.

**Contracts:**
- REQUIRES: `inputs` may contain `images` key with list of images
- ENSURES: Extracts images from inputs
- ENSURES: Formats prompt without images key
- ENSURES: Calls `self.llm._call(prompt=..., images=...)` directly
- ENSURES: Returns `{"text": response}`

---

#### `ImageProcessingPipeline`
```python
class ImageProcessingPipeline(BasePipeline):
    """Pipeline dedicated to processing and analyzing images."""
    
    # Internal chain
    _image_llm_chain: ImageLLMChain
    image_processing_chain: ChainWrapper
```

**Constructor:**
```python
def __init__(self, config: Dict[str, Any], *args, **kwargs) -> None
```

**Contracts:**
- REQUIRES: `llms['image_processing_model']` is a vision-capable LLM
- REQUIRES: `prompts['image_processing_prompt']` exists
- ENSURES: Creates `ImageLLMChain` with vision model
- ENSURES: Wraps in `ChainWrapper` for token management

**Methods:**

##### `invoke`
```python
def invoke(self, images: List[Any], **kwargs) -> PipelineOutput
```
Process a list of images.

**Contracts:**
- REQUIRES: `images` is a list of image data
- ENSURES: Logs number of images being processed
- ENSURES: Passes images through chain
- ENSURES: Returns `PipelineOutput` with extracted text

## Required Configuration

```yaml
a2rchi:
  pipeline_map:
    ImageProcessingPipeline:
      models:
        required:
          image_processing_model: <vision_model_name>
      prompts:
        required:
          image_processing_prompt: <path>
```

## Output Schema

```python
PipelineOutput(
    answer="<extracted text from images>",
    source_documents=[],
    intermediate_steps=[],
    metadata={...}  # any extra chain outputs
)
```

## Image Flow

```
1. images: List[Any] passed to invoke()
2. ChainWrapper.invoke({"images": images})
3. ImageLLMChain._call(inputs)
   - Extracts images from inputs
   - Formats prompt template
   - Calls llm._call(prompt=..., images=...)
4. Response extracted and returned
```

## Invariants

1. Uses `ImageLLMChain` instead of standard LLMChain
2. Directly calls `llm._call()` to pass images (bypasses LangChain interface)
3. Vision model must support `_call(prompt, images)` signature
4. Compatible with `HuggingFaceImageLLM`
