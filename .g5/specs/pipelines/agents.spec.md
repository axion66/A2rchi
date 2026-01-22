---
type: spec
module: a2rchi.pipelines.agents
version: "1.1"
status: draft
test_file: tests/unit/test_agents.py
source_files:
  - src/a2rchi/pipelines/agents/base_react.py
  - src/a2rchi/pipelines/agents/cms_comp_ops_agent.py
---

# Agents Spec

## Overview

LangGraph-based ReAct agents for A2rchi. Unlike classic pipelines that execute a fixed chain, agents can use tools dynamically to answer user queries.

## Dependencies

- `langgraph.graph.state.CompiledStateGraph`
- `langchain_core.messages.BaseMessage`
- `src/a2rchi/utils/output_dataclass.PipelineOutput`
- `src/a2rchi/pipelines/agents/utils/document_memory.DocumentMemory`

## Public API

### Classes

#### `BaseReActAgent`
```python
class BaseReActAgent:
    """Foundation for ReAct-style agents with tool support."""
    
    # Instance attributes
    config: Dict[str, Any]
    agent: Optional[CompiledStateGraph]
    agent_llm: Optional[Any]
    agent_prompt: Optional[str]
    _active_memory: Optional[DocumentMemory]
    _static_tools: Optional[List[Callable]]
    _active_tools: List[Callable]
```

**Constructor:**
```python
def __init__(self, config: Dict[str, Any], *args, **kwargs) -> None
```

**Contracts:**
- REQUIRES: `config["a2rchi"]["pipeline_map"]` contains entry for class name
- ENSURES: LLMs and prompts initialized
- ENSURES: `agent_llm` defaults to first available LLM if not explicitly set

**Methods:**

##### `invoke`
```python
def invoke(self, **kwargs) -> PipelineOutput
```
Synchronously execute the agent and return final output.

**Contracts:**
- ENSURES: Returns `PipelineOutput` with answer, source_documents, messages
- ENSURES: Agent graph refreshed if not already built

##### `stream`
```python
def stream(self, **kwargs) -> Iterator[PipelineOutput]
```
Stream agent updates, yielding intermediate outputs.

**Contracts:**
- ENSURES: Yields `PipelineOutput` for each graph node update
- ENSURES: Each intermediate output has `final=False`
- ENSURES: Final output has `final=True`
- ENSURES: Yields `type="chunk"` for streaming text tokens
- ENSURES: Yields `type="tool_call"` when agent invokes a tool
- ENSURES: Yields `type="tool_result"` with tool execution results

**Stream Event Types:**
```python
# Text chunk (streaming tokens)
PipelineOutput(
    answer="partial text",
    type="chunk",
    final=False,
)

# Tool invocation
PipelineOutput(
    answer="",
    tool_calls=[{"name": "tool_name", "args": {...}}],
    type="tool_call",
    final=False,
)

# Tool result
PipelineOutput(
    answer="",
    tool_results=[{"name": "tool_name", "result": "..."}],
    type="tool_result", 
    final=False,
)

# Final output (raw markdown)
PipelineOutput(
    answer="Full response in markdown",
    source_documents=[...],
    messages=[...],
    final=True,
)
```

##### `astream`
```python
async def astream(self, **kwargs) -> AsyncIterator[PipelineOutput]
```
Async version of `stream()`.

##### `refresh_agent`
```python
def refresh_agent(self, force: bool = False) -> None
```
Rebuild the agent graph.

**Contracts:**
- ENSURES: Agent graph rebuilt if `force=True` or not yet built
- ENSURES: Tools and middleware attached to graph

##### `finalize_output`
```python
def finalize_output(
    self,
    *,
    answer: str,
    memory: Optional[DocumentMemory] = None,
    messages: Optional[Sequence[BaseMessage]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tool_calls: Optional[Sequence[Dict[str, Any]]] = None,
    final: bool = True,
) -> PipelineOutput
```
Compose a `PipelineOutput` from agent execution results.

**Contracts:**
- ENSURES: `source_documents` populated from memory if provided
- ENSURES: `tool_calls` extracted from messages if not provided

---

#### `CMSCompOpsAgent`
```python
class CMSCompOpsAgent(BaseReActAgent):
    """Agent specialized for CMS CompOps ticket operations."""
```

Extends `BaseReActAgent` with CMS-specific tools:
- `search_local_files` - Search local documentation
- `search_metadata_index` - Search metadata catalog
- `fetch_catalog_document` - Retrieve full document by ID

---

## Tool Registration

Agents define tools via class attributes:

```python
class MyAgent(BaseReActAgent):
    _static_tools = [my_tool_function]
    
    def refresh_agent(self, force: bool = False):
        # Tools bound to agent graph
        self._active_tools = self._bind_tools(self._static_tools)
```

## Configuration

```yaml
pipeline_map:
  CMSCompOpsAgent:
    models:
      required:
        chat_model: "OpenAILLM"
    prompts:
      required:
        agent_prompt: "prompts/agent.prompt"
```

## PipelineOutput Fields

```python
@dataclass
class PipelineOutput:
    answer: str                    # Response text (raw markdown for streaming)
    source_documents: List[Document]
    messages: List[BaseMessage]    # Full conversation history
    metadata: Dict[str, Any]
    final: bool                    # True only for final output
    tool_calls: List[Dict]         # Tool invocations made
    type: Optional[str]            # "chunk", "tool_call", "tool_result", or None
```
