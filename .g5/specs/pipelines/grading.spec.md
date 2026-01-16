---
type: spec
module: a2rchi.pipelines.classic_pipelines.grading
version: "1.0"
status: extracted
test_file: tests/unit/test_pipelines_grading.py
source_files:
  - src/a2rchi/pipelines/classic_pipelines/grading.py
---

# Grading Pipeline Spec

## Overview

Multi-step grading pipeline that processes student submissions through summary, analysis, and final grading stages. Used for automated assignment grading with rubric-based evaluation.

## Dependencies

- `src/a2rchi/pipelines/classic_pipelines/base.BasePipeline`
- `src/a2rchi/pipelines/classic_pipelines/utils/chain_wrappers.ChainWrapper`
- `src/a2rchi/utils/output_dataclass.PipelineOutput`
- `src/data_manager/vectorstore/retrievers.SemanticRetriever`
- `langchain_core.output_parsers.StrOutputParser`

## Public API

### Classes

#### `GradingPipeline`
```python
class GradingPipeline(BasePipeline):
    """Pipeline for grading using summary, analysis, and final grade steps."""
    
    # Chains (optional except final_grade_chain)
    summary_chain: Optional[ChainWrapper] = None
    analysis_chain: Optional[ChainWrapper] = None
    final_grade_chain: ChainWrapper
    retriever: Optional[SemanticRetriever] = None
```

**Constructor:**
```python
def __init__(self, config: Dict[str, Any], *args, **kwargs) -> None
```

**Contracts:**
- REQUIRES: `prompts['final_grade_prompt']` exists
- REQUIRES: `llms['final_grade_model']` exists
- ENSURES: `summary_chain` created if `summary_prompt` exists
- ENSURES: `analysis_chain` created if `analysis_prompt` exists
- ENSURES: `final_grade_chain` always created

**Methods:**

##### `_init_chains` (protected)
```python
def _init_chains(self) -> None
```
Initialize grading chains based on available prompts.

**Chain Dependencies:**
- `summary_chain`: `submission_text` → summary
- `analysis_chain`: `submission_text`, `rubric_text`, `summary` → analysis
- `final_grade_chain`: `rubric_text`, `submission_text`, `analysis`, `additional_comments` → grade

##### `update_retriever`
```python
def update_retriever(self, vectorstore) -> None
```
Initialize SemanticRetriever for solution lookup.

**Contracts:**
- ENSURES: Creates `SemanticRetriever` with config from `dm_config["retrievers"]["semantic_retriever"]`

##### `_estimate_grader_reserved_tokens`
```python
def _estimate_grader_reserved_tokens(
    self,
    submission_text: str,
    rubric_text: str,
    summary: str,
    additional_comments: str,
) -> int
```
Estimate tokens needed for grading inputs.

**Contracts:**
- ENSURES: Returns sum of all input tokens + 300 buffer

##### `invoke`
```python
def invoke(
    self,
    submission_text: str,
    rubric_text: str,
    additional_comments: str = "",
    vectorstore=None,
    **kwargs,
) -> PipelineOutput
```
Execute the full grading pipeline.

**Contracts:**
- REQUIRES: `submission_text` is the student's work
- REQUIRES: `rubric_text` is the grading rubric
- ENSURES: Executes available chains in order: summary → retrieval → analysis → grade
- ENSURES: Uses placeholder text if optional chains missing

**Pipeline Flow:**
```
1. summary_chain(submission_text) → summary (or "No solution summary.")
2. retriever.invoke(submission_text) → reference docs
3. analysis_chain(submission, rubric, summary) → analysis (or "No preliminary analysis.")
4. final_grade_chain(rubric, submission, analysis, comments) → grade
5. Return PipelineOutput
```

## Required Configuration

```yaml
a2rchi:
  pipeline_map:
    GradingPipeline:
      max_tokens: 7000
      models:
        required:
          final_grade_model: <model_name>
        optional:
          analysis_model: <model_name>
      prompts:
        required:
          final_grade_prompt: <path>
        optional:
          summary_prompt: <path>
          analysis_prompt: <path>
```

## Output Schema

```python
PipelineOutput(
    answer="<final grade>",
    source_documents=[Document, ...],
    intermediate_steps=[summary, analysis],
    metadata={
        "summary": "...",
        "analysis": "...",
        "additional_comments": "..."
    }
)
```

## Invariants

1. Only `final_grade_chain` is required
2. Summary and analysis steps are skipped if prompts not configured
3. Uses SemanticRetriever (not HybridRetriever like QA)
4. Intermediate steps preserved for audit trail
