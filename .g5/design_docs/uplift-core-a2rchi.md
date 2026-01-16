# Uplift Core A2rchi

## Overview

Extract specs from `src/a2rchi/a2rchi.py` - the main A2rchi class that orchestrates pipelines and vectorstore connections.

## Goals

1. Extract spec from the core A2rchi class
2. Document the pipeline orchestration contracts
3. Enable spec-driven development for future changes

## Non-Goals

- Refactoring existing code
- Adding new features

## Source Files

| File | Lines | Description |
|------|-------|-------------|
| `a2rchi.py` | ~110 | Main A2rchi class - pipeline orchestration |

## Affected Specs

specs:
  - .g5/specs/a2rchi/core.spec.md

## Module Analysis

### A2rchi Class

The central orchestration class that:
- Loads configuration with model class mapping
- Creates pipeline instances dynamically
- Connects to vectorstore
- Provides invoke/stream/astream methods for pipeline execution

**Methods:**
- `__init__(pipeline, config_name)` - Initialize with pipeline name
- `update(pipeline, config_name)` - Reload config and recreate pipeline
- `_create_pipeline_instance(class_name)` - Dynamic pipeline instantiation
- `_prepare_call_kwargs(kwargs)` - Attach vectorstore to call
- `_ensure_pipeline_output(result)` - Validate return type
- `supports_stream()` - Check if pipeline has stream method
- `supports_astream()` - Check if pipeline has async stream
- `invoke(*args, **kwargs)` - Execute pipeline synchronously
- `stream(*args, **kwargs)` - Stream pipeline output
- `astream(*args, **kwargs)` - Async stream pipeline output
- `__call__` - Alias for invoke

**Dependencies:**
- `src.utils.config_loader.load_config`
- `src.a2rchi.pipelines` (dynamic import)
- `src.a2rchi.utils.output_dataclass.PipelineOutput`
- `src.a2rchi.utils.vectorstore_connector.VectorstoreConnector`
