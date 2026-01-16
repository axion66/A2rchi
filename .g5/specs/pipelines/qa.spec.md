---
type: spec
module: a2rchi.pipelines.classic_pipelines.qa
version: "1.0"
status: extracted
test_file: tests/unit/test_pipelines_qa.py
source_files:
  - src/a2rchi/pipelines/classic_pipelines/qa.py
---

# QA Pipeline Spec

## Overview

Question-answering pipeline that condenses chat history, retrieves relevant documents, and generates answers. The primary pipeline for conversational Q&A use cases.

## Dependencies

- `src/a2rchi/pipelines/classic_pipelines/base.BasePipeline`
- `src/a2rchi/pipelines/classic_pipelines/utils/chain_wrappers.ChainWrapper`
- `src/a2rchi/pipelines/classic_pipelines/utils/history_utils`
- `src/a2rchi/utils/output_dataclass.PipelineOutput`
- `src/data_manager/vectorstore/retrievers.HybridRetriever`
- `langchain_classic.chains.combine_documents.stuff.create_stuff_documents_chain`
- `langchain_core.output_parsers.StrOutputParser`

## Public API

### Classes

#### `QAPipeline`
```python
class QAPipeline(BasePipeline):
    """Pipeline that condenses history, retrieves documents, and answers questions."""
    
    # Chains initialized in __init__
    condense_chain: ChainWrapper  # History condensation
    chat_chain: ChainWrapper      # Answer generation
    retriever: HybridRetriever    # Document retrieval
```

**Constructor:**
```python
def __init__(self, config: Dict[str, Any], *args, **kwargs) -> None
```

**Contracts:**
- REQUIRES: `prompts['condense_prompt']` exists
- REQUIRES: `prompts['chat_prompt']` exists
- REQUIRES: `llms['condense_model']` exists
- REQUIRES: `llms['chat_model']` exists
- ENSURES: `condense_chain` configured with history input
- ENSURES: `chat_chain` configured with question and retriever_output inputs

**Methods:**

##### `_prepare_inputs`
```python
def _prepare_inputs(self, history: Any, **kwargs) -> Dict[str, Any]
```
Extract question and format history from raw input.

**Contracts:**
- ENSURES: Returns dict with `question`, `history`, `full_history`
- ENSURES: `question` is last message from history (second element of last tuple)
- ENSURES: `history` is all messages except the last one
- ENSURES: Logs error if no question found

##### `update_retriever`
```python
def update_retriever(self, vectorstore) -> None
```
Initialize HybridRetriever with BM25 + semantic search.

**Contracts:**
- ENSURES: Creates `HybridRetriever` with config from `dm_config["retrievers"]`
- ENSURES: Uses default `k=5` if not configured

##### `invoke`
```python
def invoke(self, **kwargs) -> PipelineOutput
```
Execute the full QA pipeline.

**Contracts:**
- REQUIRES: `kwargs["history"]` contains conversation history
- ENSURES: Updates retriever if `vectorstore` provided
- ENSURES: Condenses history → retrieves docs → generates answer
- ENSURES: Returns `PipelineOutput` with answer, documents, and metadata

**Pipeline Flow:**
```
1. _prepare_inputs(history) → {question, history, full_history}
2. condense_chain.invoke({history, ...}) → condensed question
3. retriever.invoke(condensed_question) → [(doc, score), ...]
4. chat_chain.invoke({question, retriever_output, ...}) → answer
5. Return PipelineOutput
```

## Required Configuration

```yaml
a2rchi:
  pipeline_map:
    QAPipeline:
      max_tokens: 7000
      models:
        required:
          condense_model: <model_name>
          chat_model: <model_name>
      prompts:
        required:
          condense_prompt: <path>
          chat_prompt: <path>
data_manager:
  retrievers:
    hybrid_retriever:
      num_documents_to_retrieve: 5
      bm25_weight: 0.6
      semantic_weight: 0.4
    bm25_retriever:
      k1: 0.5
      b: 0.75
```

## Output Schema

```python
PipelineOutput(
    answer="...",
    source_documents=[Document, ...],
    messages=[],
    metadata={
        "retriever_scores": [float, ...],
        "condensed_output": "...",
        "question": "..."
    }
)
```

## Invariants

1. Always uses HybridRetriever (BM25 + semantic)
2. History is condensed before retrieval
3. Empty history results in empty question (with error log)
