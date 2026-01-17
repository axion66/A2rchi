---
spec_id: a2rchi
type: package
status: extracted
children:
  - a2rchi/core
  - a2rchi/models
  - a2rchi/pipelines
---

# A2rchi Package

Core LLM orchestration framework. Connects models, pipelines, and vectorstores.

## Exports

```python
from src.a2rchi import A2rchi
from src.a2rchi.models import *
from src.a2rchi.pipelines import *
```

## Structure

```
a2rchi/
├── __init__.py
├── a2rchi.py          # A2rchi orchestrator class
├── models/            # LLM implementations (8 specs)
├── pipelines/         # Processing pipelines (8 specs)
└── utils/
    └── output_dataclass.py
    └── vectorstore_connector.py
```

## A2rchi Class

The central orchestrator:

```python
class A2rchi:
    def __init__(pipeline: str, **kwargs)
    def __call__(*args, **kwargs) -> PipelineOutput
    def update(pipeline: str = None, config_name: str = None)
    def stream(*args, **kwargs) -> Iterator[str]
```

## Data Flow

```
A2rchi.__call__()
    │
    ├── VectorstoreConnector.get_vectorstore()
    │
    └── Pipeline.invoke(vectorstore=vs, ...)
            │
            ├── LLM.invoke(prompt)
            │
            └── Retriever.get_relevant_documents(query)
```

## Configuration

```yaml
a2rchi:
  pipeline_map:
    QAPipeline:
      models: { required: { main_llm: "OpenAILLM" } }
      prompts: { required: { qa: "prompts/qa.prompt" } }
  model_class_map:
    OpenAILLM:
      class: OpenAILLM
      kwargs: { model_name: "gpt-4" }
```

## Child Modules

- **models/** - 8 LLM implementations (OpenAI, Anthropic, HuggingFace, etc.)
- **pipelines/** - 4 pipelines + utilities (QA, Grading, Image, Agents)
