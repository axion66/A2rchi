---
spec_id: a2rchi/pipelines
type: module
status: extracted
children:
  - a2rchi/pipelines/base
  - a2rchi/pipelines/qa
  - a2rchi/pipelines/grading
  - a2rchi/pipelines/image
  - a2rchi/pipelines/chain-wrapper
  - a2rchi/pipelines/token-limiter
  - a2rchi/pipelines/prompt-utils
  - a2rchi/pipelines/safety
  - a2rchi/pipelines/agents
---

# Pipelines Module

Processing pipelines for A2rchi. Each pipeline orchestrates LLMs and prompts for a specific task.

## Exports

```python
from src.a2rchi.pipelines import (
    BasePipeline,
    QAPipeline,
    GradingPipeline,
    ImageProcessingPipeline,
    BaseAgent,
    CMSCompOpsAgent,
)
```

## Pipeline Hierarchy

```
BasePipeline
├── QAPipeline              # RAG question-answering
├── GradingPipeline         # Student submission grading
└── ImageProcessingPipeline # Vision-language processing

BaseAgent
└── CMSCompOpsAgent         # CMS operations agent
```

## Submodules

```
pipelines/
├── __init__.py
├── classic_pipelines/
│   ├── base.py           # BasePipeline
│   ├── qa.py             # QAPipeline
│   ├── grading.py        # GradingPipeline
│   ├── image_processing.py
│   ├── chain.py          # ChainWrapper
│   ├── token_limiter.py
│   └── utils/
│       ├── prompt_formatters.py
│       ├── prompt_validator.py
│       ├── prompt_utils.py
│       ├── safety_checker.py
│       └── history_utils.py
└── agents/
    ├── base.py
    ├── cms_comp_ops_agent.py
    └── tools/
```

## Pipeline Interface

All pipelines implement:

```python
class BasePipeline:
    def __init__(self, config: Dict) -> None
    def update_retriever(self, vectorstore) -> None
    def invoke(self, *args, **kwargs) -> PipelineOutput
```

## PipelineOutput

```python
@dataclass
class PipelineOutput:
    answer: str
    source_documents: List[Document]
    intermediate_steps: List[Any]
```

## Configuration

Pipelines read from `config["a2rchi"]["pipeline_map"][PipelineName]`:

```yaml
pipeline_map:
  QAPipeline:
    models:
      required: { main_llm: "OpenAILLM" }
    prompts:
      required: { qa_prompt: "prompts/qa.prompt" }
```
