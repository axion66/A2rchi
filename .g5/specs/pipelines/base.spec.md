---
type: spec
module: a2rchi.pipelines.classic_pipelines.base
version: "1.0"
status: extracted
test_file: tests/unit/test_pipelines_base.py
source_files:
  - src/a2rchi/pipelines/classic_pipelines/base.py
---

# Base Pipeline Spec

## Overview

Foundation class for all A2rchi pipelines. Provides common initialization for LLMs and prompts based on configuration, and defines the standard pipeline interface.

## Dependencies

- `src/a2rchi/pipelines/classic_pipelines/utils/prompt_utils.read_prompt`
- `src/a2rchi/pipelines/classic_pipelines/utils/prompt_validator.ValidatedPromptTemplate`
- `src/a2rchi/utils/output_dataclass.PipelineOutput`
- `src/utils/logging`

## Public API

### Classes

#### `BasePipeline`
```python
class BasePipeline:
    """Foundational structure for building pipeline classes."""
    
    # Instance attributes set in __init__
    config: Dict[str, Any]
    a2rchi_config: Dict[str, Any]
    dm_config: Dict[str, Any]
    pipeline_config: Dict[str, Any]
    llms: Dict[str, Any]
    prompts: Dict[str, ValidatedPromptTemplate]
    
    # Set via update_retriever (not in __init__)
    # retriever: Optional[Any]
```

**Constructor:**
```python
def __init__(self, config: Dict[str, Any], *args, **kwargs) -> None
```

**Contracts:**
- REQUIRES: `config` contains `a2rchi` and `data_manager` keys
- REQUIRES: `config["a2rchi"]["pipeline_map"]` contains entry for `self.__class__.__name__`
- ENSURES: `self.llms` populated with model instances
- ENSURES: `self.prompts` populated with validated templates

**Methods:**

##### `update_retriever`
```python
def update_retriever(self, vectorstore) -> None
```
Update the retriever with a new vectorstore. Default implementation sets to None.

##### `invoke`
```python
def invoke(self, *args, **kwargs) -> PipelineOutput
```
Execute the pipeline. Default implementation returns placeholder response.

**Contracts:**
- ENSURES: Returns `PipelineOutput` instance

##### `_init_llms` (protected)
```python
def _init_llms(self) -> None
```
Initialize language models from configuration.

**Contracts:**
- REQUIRES: `self.a2rchi_config["model_class_map"]` exists
- ENSURES: Creates model instances from `pipeline_config["models"]["required"]` and `["optional"]`
- ENSURES: Reuses existing model instances if same class already initialized
- ENSURES: Logs model initialization details

##### `_init_prompts` (protected)
```python
def _init_prompts(self) -> None
```
Initialize prompts from configuration.

**Contracts:**
- REQUIRES: `pipeline_config["prompts"]` exists (can be empty)
- ENSURES: Loads prompt templates from file paths
- ENSURES: Raises `FileNotFoundError` for missing required prompts
- ENSURES: Logs warning for missing optional prompts
- ENSURES: Wraps templates in `ValidatedPromptTemplate`

## Configuration Schema

```yaml
a2rchi:
  model_class_map:
    <model_name>:
      class: <ModelClass>
      kwargs: {...}
  pipeline_map:
    <PipelineClass>:
      models:
        required:
          <alias>: <model_name>
        optional:
          <alias>: <model_name>
      prompts:
        required:
          <alias>: <path>
        optional:
          <alias>: <path>
data_manager:
  # retriever configuration
```

## Invariants

1. LLM instances are shared if same class is requested multiple times
2. Prompts are always wrapped in `ValidatedPromptTemplate`
3. Missing required prompts cause immediate failure
4. Missing optional prompts are silently skipped (with warning)

## Usage Pattern

```python
class MyPipeline(BasePipeline):
    def __init__(self, config, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        # self.llms and self.prompts now available
        self.my_chain = self.prompts['my_prompt'] | self.llms['my_model']
    
    def invoke(self, **kwargs) -> PipelineOutput:
        result = self.my_chain.invoke(kwargs)
        return PipelineOutput(answer=result, ...)
```
