---
spec_id: a2rchi/core
type: class
source_files:
  - src/a2rchi/a2rchi.py
test_file: null
status: extracted
---

# A2rchi Core

> ⚠️ **AUTO-GENERATED FROM CODE**: Review for accuracy.

## Overview

Central orchestration class of the A2rchi framework. Connects configuration, pipelines, and vectorstore to provide a unified interface for LLM-powered question answering.

## Structured Design Doc

### Class: A2rchi

#### Constructor

##### `__init__(pipeline: str, *args, config_name: str = None, **kwargs)`

Initialize A2rchi with a named pipeline.

**Contracts:**
- PRE: `pipeline` is a valid pipeline class name in `src.a2rchi.pipelines`
- POST: `self.config` loaded with model class mapping
- POST: `self.pipeline` is instantiated pipeline object
- POST: `self.vs_connector` is VectorstoreConnector instance
- ERROR: `ValueError` if pipeline class not found

#### Methods

##### `update(pipeline: str = None, config_name: str = None) -> None`

Reload configuration and optionally switch pipeline.

**Contracts:**
- POST: `self.config` reloaded from config file
- POST: If `pipeline` provided, `self.pipeline_name` updated
- POST: `self.pipeline` recreated with new config

##### `_create_pipeline_instance(class_name: str, *args, **kwargs) -> Pipeline`

Dynamically instantiate a pipeline class.

**Contracts:**
- PRE: `class_name` exists as attribute on `src.a2rchi.pipelines`
- POST: Returns instantiated pipeline object
- ERROR: `ValueError` if class not found in module
- ERROR: `RuntimeError` if instantiation fails

##### `_prepare_call_kwargs(kwargs: dict) -> dict`

Attach fresh vectorstore to call kwargs.

**Contracts:**
- POST: Returns new dict with all original kwargs
- POST: `result["vectorstore"]` is fresh vectorstore from connector

##### `_ensure_pipeline_output(result: Any) -> PipelineOutput`

Validate pipeline returns correct type.

**Contracts:**
- PRE: `result` should be PipelineOutput
- POST: Returns `result` unchanged if valid
- ERROR: `TypeError` if result is not PipelineOutput

##### `supports_stream() -> bool`

Check if pipeline supports synchronous streaming.

**Contracts:**
- POST: Returns True if `self.pipeline.stream` is callable
- POST: Returns False otherwise

##### `supports_astream() -> bool`

Check if pipeline supports async streaming.

**Contracts:**
- POST: Returns True if `self.pipeline.astream` is callable
- POST: Returns False otherwise

##### `invoke(*args, **kwargs) -> PipelineOutput`

Execute pipeline synchronously.

**Contracts:**
- POST: Vectorstore attached to kwargs
- POST: Returns PipelineOutput from pipeline
- ERROR: `TypeError` if pipeline returns wrong type

##### `stream(*args, **kwargs) -> Generator[PipelineOutput]`

Stream pipeline output synchronously.

**Contracts:**
- PRE: `supports_stream()` returns True
- POST: Yields PipelineOutput for each event
- ERROR: `AttributeError` if pipeline doesn't support stream

##### `astream(*args, **kwargs) -> AsyncGenerator[PipelineOutput]`

Stream pipeline output asynchronously.

**Contracts:**
- PRE: `supports_astream()` returns True
- POST: Yields PipelineOutput for each event
- ERROR: `AttributeError` if pipeline doesn't support astream

##### `__call__(*args, **kwargs) -> PipelineOutput`

Alias for invoke().

**Contracts:**
- POST: Same as `invoke()`

## Invariants

- `self.pipeline` is always a valid pipeline instance after construction
- `self.config` always has model classes mapped (not strings)
- All public methods return/yield PipelineOutput

## Guardrails

- Pipeline classes loaded dynamically via getattr
- Vectorstore refreshed on each call (not cached)
- Config reloaded on update() calls

## Testing Contracts

- Init with valid pipeline creates instance
- Init with invalid pipeline raises ValueError
- invoke returns PipelineOutput
- stream raises AttributeError if unsupported
- astream raises AttributeError if unsupported
