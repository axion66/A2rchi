# Uplift Classic Pipelines

## Overview

Extract G5 specs from the classic pipelines module (`src/a2rchi/pipelines/classic_pipelines/`). This module provides the main pipeline implementations for QA, grading, and image processing workflows.

## Goals

1. Extract specs for all pipeline classes and utilities
2. Document the chain wrapping and token limiting mechanisms
3. Document the prompt formatting and validation system
4. Enable G5 workflow for future pipeline development

## Non-Goals

- Refactoring existing code
- Adding new pipeline types
- Changing existing behavior

## Module Structure

```
src/a2rchi/pipelines/classic_pipelines/
├── base.py              # BasePipeline - foundation for all pipelines
├── chains.py            # ImageLLMChain - custom chain for images
├── grading.py           # GradingPipeline - multi-step grading
├── image_processing.py  # ImageProcessingPipeline - vision models
├── qa.py                # QAPipeline - question answering
└── utils/
    ├── callback_handlers.py  # LangChain callbacks
    ├── chain_wrappers.py     # ChainWrapper - harmonizes chains
    ├── history_utils.py      # Chat history formatting
    ├── prompt_formatters.py  # PromptFormatter - model-specific formatting
    ├── prompt_utils.py       # read_prompt function
    ├── prompt_validator.py   # ValidatedPromptTemplate
    ├── safety_checker.py     # check_safety wrapper
    └── token_limiter.py      # TokenLimiter - context management
```

## Architecture

### Pipeline Hierarchy

```
BasePipeline (base.py)
├── QAPipeline (qa.py) - condense + retrieve + answer
├── GradingPipeline (grading.py) - summary + analysis + grade
└── ImageProcessingPipeline (image_processing.py) - vision LLM
```

### Key Components

1. **BasePipeline**: Initializes LLMs and prompts from config
2. **ChainWrapper**: Wraps LangChain chains with token limiting
3. **TokenLimiter**: Manages context window limits
4. **PromptFormatter**: Applies model-specific formatting
5. **ValidatedPromptTemplate**: Validates prompt variables

## Specs to Create

| Spec | Class(es) | Type |
|------|-----------|------|
| `pipelines/base.spec.md` | `BasePipeline` | Abstract base |
| `pipelines/qa.spec.md` | `QAPipeline` | Pipeline |
| `pipelines/grading.spec.md` | `GradingPipeline` | Pipeline |
| `pipelines/image.spec.md` | `ImageProcessingPipeline`, `ImageLLMChain` | Pipeline |
| `pipelines/chain-wrapper.spec.md` | `ChainWrapper` | Utility |
| `pipelines/token-limiter.spec.md` | `TokenLimiter` | Utility |
| `pipelines/prompt-utils.spec.md` | `PromptFormatter`, `ValidatedPromptTemplate`, `read_prompt` | Utility |
| `pipelines/safety.spec.md` | `check_safety` | Utility |

## Success Criteria

- [ ] All pipeline classes have specs
- [ ] Chain/token management documented
- [ ] Prompt formatting system documented
- [ ] Integration patterns clear
