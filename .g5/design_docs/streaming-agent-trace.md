# Design Document: Streaming Agent Trace Output

## Summary

Expose the full agent execution trace (tool calls, tool outputs, LLM reasoning, intermediate steps) to the chat UI in real-time, similar to Claude Code's transparent agent visualization. Users see the "thinking process" not just the final answer.

---

## User Intent

The user wants:
1. **Full agent transparency** - See every tool call, LLM reasoning step, and intermediate output as they happen
2. **Verbose mode settings** - Toggle between minimal (final answer only) and verbose (full trace) views
3. **Cancellation support** - Ability to cancel/interrupt agent execution mid-stream
4. **Persistent traces** - Store the complete execution trace in the database for replay/analysis

---

## Current State

### Existing Streaming Infrastructure
- [a2rchi.py](src/a2rchi/a2rchi.py) exposes `stream()` and `astream()` methods that yield `PipelineOutput` objects
- [base_react.py](src/a2rchi/pipelines/agents/base_react.py#L103-L137) streams LangGraph events via `agent.stream(agent_inputs, stream_mode="messages")`
- `PipelineOutput` already has a `tool_calls` field that captures tool execution data

### Current Chat App Streaming
- [app.py#L962-L1020](src/interfaces/chat_app/app.py#L962-L1020) has `_stream_events_from_output()` that can extract tool calls
- Streaming endpoint already supports `include_agent_steps` and `include_tool_steps` flags
- Tool calls are stored via `insert_tool_calls_from_messages()` at [app.py#L829](src/interfaces/chat_app/app.py#L829)

### Current Limitations
1. **No real-time tool visualization** - Tool steps extracted but not surfaced to UI during streaming
2. **No verbose mode toggle** - Settings exist but don't control trace visibility
3. **No cancellation** - Once streaming starts, no way to abort
4. **Limited event types** - Only `text` and `step` events, no structured agent trace events

---

## Proposed Design

### UX Flow (Claude Code Style)

```
User: "Find all files with TODO comments and summarize them"

┌─ 🔧 Tool Call: grep_search                                    [running]
│  Arguments: {"query": "TODO", "isRegexp": false}
│  ▼ Show output
└─

┌─ 🔧 Tool Call: grep_search                                    [complete]
│  Arguments: {"query": "TODO", "isRegexp": false}
│  ▼ Found 12 matches in 5 files
│    └─ src/utils/config.py:45: # TODO: add validation
│    └─ src/data_manager/scheduler.py:23: # TODO: retry logic
│    └─ ... (click to expand)
└─

┌─ 📄 Tool Call: read_file                                      [running]
│  Arguments: {"filePath": "/src/utils/config.py", "startLine": 40, "endLine": 60}
└─

┌─ 💭 Thinking...
│  "I found TODOs related to validation and retry logic..."
└─

┌─ ✨ Response
│  Here's a summary of the 12 TODOs found:
│  1. **Validation improvements** (3 items)
│     - config.py:45 - Add input validation
│  ...
└─
```

### Event Schema

Extend the SSE stream with structured trace events:

```typescript
// Base event structure
interface StreamEvent {
  type: "text" | "tool_start" | "tool_output" | "tool_end" | "thinking" | "error" | "final" | "cancelled";
  conversation_id: number;
  timestamp: string;  // ISO 8601
}

// Tool execution events
interface ToolStartEvent extends StreamEvent {
  type: "tool_start";
  tool_call_id: string;
  tool_name: string;
  tool_args: Record<string, any>;
}

interface ToolOutputEvent extends StreamEvent {
  type: "tool_output";
  tool_call_id: string;
  output: string;
  truncated: boolean;
  full_length?: number;  // Original length if truncated
}

interface ToolEndEvent extends StreamEvent {
  type: "tool_end";
  tool_call_id: string;
  status: "success" | "error";
  duration_ms?: number;
  error_message?: string;
}

// LLM reasoning events
interface ThinkingEvent extends StreamEvent {
  type: "thinking";
  content: string;  // Intermediate reasoning from agent
}

// Text streaming (existing, enhanced)
interface TextEvent extends StreamEvent {
  type: "text";
  content: string;
  delta: boolean;  // true = incremental chunk, false = full replacement
}

// Control events
interface FinalEvent extends StreamEvent {
  type: "final";
  message_id: number;
  user_message_id: number;
  trace_id: string;  // Reference to stored trace
}

interface CancelledEvent extends StreamEvent {
  type: "cancelled";
  reason: string;
  partial_message_id?: number;  // If partial response was saved
}

interface ErrorEvent extends StreamEvent {
  type: "error";
  error_code: string;
  error_message: string;
}
```

### Verbose Mode Settings

Add to user preferences (stored in localStorage, optionally synced to backend):

```typescript
interface TraceSettings {
  // Display mode
  verbose_mode: "minimal" | "normal" | "verbose";
  //   minimal: Final answer only, no tool calls shown
  //   normal: Tool calls shown collapsed, expand on click
  //   verbose: Tool calls expanded by default, full output

  // Auto-collapse thresholds
  auto_collapse_output_lines: number;  // Default: 10
  auto_collapse_tool_count: number;    // Default: 5 (collapse all if > N tools)

  // Content limits (client-side)
  max_tool_output_preview: number;     // Default: 500 chars
  max_thinking_preview: number;        // Default: 200 chars
}
```

Settings UI in existing settings panel:
```
Agent Transparency
├─ ○ Minimal (final answer only)
├─ ● Normal (show tool calls, collapsed)
├─ ○ Verbose (show everything expanded)
│
└─ [ ] Auto-collapse when > 5 tool calls
```

---

## Database Schema

### New Table: `agent_traces`

Store the complete execution trace for replay and analysis:

```sql
CREATE TABLE agent_traces (
    trace_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id INTEGER NOT NULL REFERENCES conversations(id),
    message_id      INTEGER NOT NULL,  -- The final assistant message
    user_message_id INTEGER NOT NULL,  -- The triggering user message
    
    -- Denormalized for quick access
    config_id       INTEGER REFERENCES configs(id),
    pipeline_name   VARCHAR(255),
    
    -- Trace data
    events          JSONB NOT NULL,    -- Array of all StreamEvents
    
    -- Execution metadata
    started_at      TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at    TIMESTAMP WITH TIME ZONE,
    status          VARCHAR(50) NOT NULL DEFAULT 'running',  -- running, completed, cancelled, error
    
    -- Aggregate stats
    total_tool_calls    INTEGER DEFAULT 0,
    total_tokens_used   INTEGER,
    total_duration_ms   INTEGER,
    
    -- Cancellation info
    cancelled_by        VARCHAR(255),  -- 'user' | 'timeout' | 'error'
    cancellation_reason TEXT,
    
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_agent_traces_conversation ON agent_traces(conversation_id);
CREATE INDEX idx_agent_traces_message ON agent_traces(message_id);
CREATE INDEX idx_agent_traces_status ON agent_traces(status);
CREATE INDEX idx_agent_traces_created ON agent_traces(created_at);
```

### Events JSONB Structure

```json
{
  "events": [
    {
      "type": "tool_start",
      "tool_call_id": "tc_001",
      "tool_name": "grep_search",
      "tool_args": {"query": "TODO"},
      "timestamp": "2026-01-22T10:30:00.123Z"
    },
    {
      "type": "tool_output",
      "tool_call_id": "tc_001",
      "output": "Found 12 matches...",
      "truncated": true,
      "full_length": 4523,
      "timestamp": "2026-01-22T10:30:01.456Z"
    },
    {
      "type": "tool_end",
      "tool_call_id": "tc_001",
      "status": "success",
      "duration_ms": 1333,
      "timestamp": "2026-01-22T10:30:01.456Z"
    },
    {
      "type": "text",
      "content": "Here's a summary...",
      "delta": false,
      "timestamp": "2026-01-22T10:30:05.789Z"
    }
  ]
}
```

---

## Backend Implementation

### 1. Enhanced Pipeline Output Events

Modify `BaseReActAgent.stream()` to yield richer events:

```python
# src/a2rchi/pipelines/agents/base_react.py

def stream(self, **kwargs) -> Iterator[PipelineOutput]:
    """Stream agent updates with full trace information."""
    agent_inputs = self._prepare_agent_inputs(**kwargs)
    if self.agent is None:
        self.refresh_agent(force=True)

    active_tool_calls: Dict[str, float] = {}  # tool_call_id -> start_time

    for event in self.agent.stream(agent_inputs, stream_mode="messages"):
        messages = self._extract_messages(event)
        if not messages:
            continue
            
        message = messages[-1]
        
        # Detect tool call start
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                tc_id = tc.get("id", "")
                if tc_id and tc_id not in active_tool_calls:
                    active_tool_calls[tc_id] = time.time()
                    yield self.finalize_output(
                        answer="",
                        memory=self.active_memory,
                        messages=messages,
                        metadata={
                            "event_type": "tool_start",
                            "tool_call_id": tc_id,
                            "tool_name": tc.get("name"),
                            "tool_args": tc.get("args", {}),
                        },
                        final=False,
                    )
        
        # Detect tool result
        if hasattr(message, "tool_call_id") and message.tool_call_id:
            tc_id = message.tool_call_id
            duration_ms = None
            if tc_id in active_tool_calls:
                duration_ms = int((time.time() - active_tool_calls[tc_id]) * 1000)
                del active_tool_calls[tc_id]
            
            yield self.finalize_output(
                answer="",
                memory=self.active_memory,
                messages=messages,
                metadata={
                    "event_type": "tool_output",
                    "tool_call_id": tc_id,
                    "output": self._message_content(message),
                },
                final=False,
            )
            yield self.finalize_output(
                answer="",
                memory=self.active_memory,
                messages=messages,
                metadata={
                    "event_type": "tool_end",
                    "tool_call_id": tc_id,
                    "status": "success",
                    "duration_ms": duration_ms,
                },
                final=False,
            )
        
        # AI content (text or thinking)
        msg_type = str(getattr(message, "type", "")).lower()
        if msg_type in {"ai", "assistant"}:
            content = self._message_content(message)
            if content:
                yield self.finalize_output(
                    answer=content,
                    memory=self.active_memory,
                    messages=messages,
                    metadata={"event_type": "text"},
                    final=False,
                )
    
    # Final output
    yield self.finalize_output(
        answer=latest_text,
        memory=self.active_memory,
        messages=latest_messages,
        metadata={"event_type": "final"},
        tool_calls=self._extract_tool_calls(latest_messages),
        final=True,
    )
```

### 2. Chat App Streaming Endpoint

Modify `_stream_pipeline()` to emit structured trace events:

```python
# src/interfaces/chat_app/app.py

def _stream_pipeline(self, context: StreamContext) -> Iterator[str]:
    """Stream with full agent trace support."""
    trace_events: List[Dict[str, Any]] = []
    trace_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)
    
    # Create trace record
    self._create_agent_trace(
        trace_id=trace_id,
        conversation_id=context.conversation_id,
        user_message_id=context.user_message_id,
        config_id=context.config_id,
        pipeline_name=context.pipeline_name,
        started_at=started_at,
    )
    
    try:
        for output in a2rchi.stream(...):
            event_type = output.metadata.get("event_type", "text")
            
            event = self._build_stream_event(
                event_type=event_type,
                output=output,
                conversation_id=context.conversation_id,
            )
            trace_events.append(event)
            
            # Yield SSE event
            yield f"data: {json.dumps(event)}\n\n"
            
            if output.final:
                # Finalize trace
                self._complete_agent_trace(
                    trace_id=trace_id,
                    events=trace_events,
                    message_id=a2rchi_message_id,
                    status="completed",
                )
                
                # Send final event with trace reference
                final_event = {
                    "type": "final",
                    "message_id": a2rchi_message_id,
                    "user_message_id": context.user_message_id,
                    "trace_id": trace_id,
                    "conversation_id": context.conversation_id,
                }
                yield f"data: {json.dumps(final_event)}\n\n"
                
    except GeneratorExit:
        # User cancelled
        self._complete_agent_trace(
            trace_id=trace_id,
            events=trace_events,
            status="cancelled",
            cancelled_by="user",
        )
        yield f"data: {json.dumps({'type': 'cancelled', 'reason': 'user'})}\n\n"
        raise
```

### 3. Cancellation Endpoint

```python
# src/interfaces/chat_app/app.py

@self.app.route("/api/cancel_stream", methods=["POST"])
def cancel_stream():
    """Cancel an active streaming request."""
    data = request.get_json()
    conversation_id = data.get("conversation_id")
    trace_id = data.get("trace_id")
    
    # Set cancellation flag (checked by streaming generator)
    self._set_cancellation_flag(conversation_id, trace_id)
    
    return jsonify({"status": "cancellation_requested"})
```

### 4. Trace Retrieval Endpoint

```python
@self.app.route("/api/trace/<trace_id>", methods=["GET"])
def get_trace(trace_id: str):
    """Retrieve a stored agent trace for replay."""
    trace = self._get_agent_trace(trace_id)
    if not trace:
        return jsonify({"error": "Trace not found"}), 404
    return jsonify(trace)
```

---

## Frontend Implementation

### 1. Trace State Management

```javascript
// chat.js - Add to state
const TraceState = {
    activeTraces: new Map(),  // conversation_id -> { trace_id, events: [], status }
    settings: {
        verbose_mode: 'normal',  // 'minimal' | 'normal' | 'verbose'
        auto_collapse_output_lines: 10,
        auto_collapse_tool_count: 5,
        max_tool_output_preview: 500,
    },
    cancellationController: null,  // AbortController for active stream
};
```

### 2. Event Stream Handler

```javascript
function handleStreamEvent(event, conversationId) {
    const trace = TraceState.activeTraces.get(conversationId);
    
    switch (event.type) {
        case 'tool_start':
            renderToolStart(event, conversationId);
            break;
        case 'tool_output':
            updateToolOutput(event, conversationId);
            break;
        case 'tool_end':
            finalizeToolCall(event, conversationId);
            break;
        case 'thinking':
            renderThinking(event, conversationId);
            break;
        case 'text':
            appendText(event, conversationId);
            break;
        case 'final':
            finalizeResponse(event, conversationId);
            break;
        case 'cancelled':
            handleCancellation(event, conversationId);
            break;
        case 'error':
            handleError(event, conversationId);
            break;
    }
    
    // Store event in trace
    if (trace) {
        trace.events.push(event);
    }
}
```

### 3. Tool Call UI Components

```javascript
function renderToolStart(event, conversationId) {
    const container = getOrCreateTraceContainer(conversationId);
    
    const toolBlock = document.createElement('div');
    toolBlock.className = 'tool-block tool-running';
    toolBlock.dataset.toolCallId = event.tool_call_id;
    toolBlock.innerHTML = `
        <div class="tool-header">
            <span class="tool-icon">🔧</span>
            <span class="tool-name">${escapeHtml(event.tool_name)}</span>
            <span class="tool-status">
                <span class="spinner"></span> Running...
            </span>
        </div>
        <div class="tool-args collapsible collapsed">
            <div class="tool-args-label">Arguments</div>
            <pre><code>${formatToolArgs(event.tool_args)}</code></pre>
        </div>
        <div class="tool-output collapsible collapsed">
            <div class="tool-output-label">Output</div>
            <pre><code class="output-content"></code></pre>
        </div>
    `;
    
    container.appendChild(toolBlock);
    
    // Auto-expand based on verbose mode
    if (TraceState.settings.verbose_mode === 'verbose') {
        toolBlock.querySelector('.tool-args').classList.remove('collapsed');
    }
}

function updateToolOutput(event, conversationId) {
    const toolBlock = document.querySelector(
        `.tool-block[data-tool-call-id="${event.tool_call_id}"]`
    );
    if (!toolBlock) return;
    
    const outputEl = toolBlock.querySelector('.output-content');
    let displayText = event.output;
    
    // Truncate if needed
    if (displayText.length > TraceState.settings.max_tool_output_preview) {
        displayText = displayText.slice(0, TraceState.settings.max_tool_output_preview) + '...';
    }
    
    outputEl.textContent = displayText;
    
    // Show output section
    toolBlock.querySelector('.tool-output').classList.remove('collapsed');
    
    // Add truncation indicator
    if (event.truncated) {
        const truncLabel = document.createElement('div');
        truncLabel.className = 'truncation-notice';
        truncLabel.textContent = `Showing ${TraceState.settings.max_tool_output_preview} of ${event.full_length} chars`;
        toolBlock.querySelector('.tool-output').appendChild(truncLabel);
    }
}

function finalizeToolCall(event, conversationId) {
    const toolBlock = document.querySelector(
        `.tool-block[data-tool-call-id="${event.tool_call_id}"]`
    );
    if (!toolBlock) return;
    
    toolBlock.classList.remove('tool-running');
    toolBlock.classList.add(event.status === 'success' ? 'tool-success' : 'tool-error');
    
    const statusEl = toolBlock.querySelector('.tool-status');
    if (event.status === 'success') {
        statusEl.innerHTML = `<span class="checkmark">✓</span> ${event.duration_ms}ms`;
    } else {
        statusEl.innerHTML = `<span class="error-icon">✗</span> Error`;
        if (event.error_message) {
            const errorEl = document.createElement('div');
            errorEl.className = 'tool-error-message';
            errorEl.textContent = event.error_message;
            toolBlock.appendChild(errorEl);
        }
    }
    
    // Auto-collapse if in normal mode and many tools
    const toolCount = document.querySelectorAll('.tool-block').length;
    if (TraceState.settings.verbose_mode === 'normal' && 
        toolCount > TraceState.settings.auto_collapse_tool_count) {
        toolBlock.querySelector('.tool-output').classList.add('collapsed');
    }
}
```

### 4. Cancel Button

```javascript
function renderCancelButton(conversationId) {
    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'cancel-stream-btn';
    cancelBtn.innerHTML = '⏹ Stop';
    cancelBtn.onclick = () => cancelStream(conversationId);
    return cancelBtn;
}

async function cancelStream(conversationId) {
    const trace = TraceState.activeTraces.get(conversationId);
    if (!trace) return;
    
    // Abort fetch request
    if (TraceState.cancellationController) {
        TraceState.cancellationController.abort();
    }
    
    // Notify server
    await fetch('/api/cancel_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            conversation_id: conversationId,
            trace_id: trace.trace_id,
        }),
    });
}
```

### 5. CSS Styling

```css
/* Tool call blocks */
.tool-block {
    margin: 8px 0;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
    font-size: 13px;
}

.tool-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: var(--bg-secondary);
    cursor: pointer;
}

.tool-icon { font-size: 14px; }

.tool-name {
    font-weight: 600;
    font-family: var(--font-mono);
}

.tool-status {
    margin-left: auto;
    font-size: 12px;
    color: var(--text-secondary);
}

.tool-running .spinner {
    display: inline-block;
    width: 12px;
    height: 12px;
    border: 2px solid var(--border-color);
    border-top-color: var(--accent-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.tool-success .checkmark { color: var(--success-color); }
.tool-error .error-icon { color: var(--error-color); }

.tool-args, .tool-output {
    border-top: 1px solid var(--border-color);
}

.collapsible {
    max-height: 300px;
    overflow: hidden;
    transition: max-height 0.3s ease;
}

.collapsible.collapsed {
    max-height: 0;
    border-top: none;
}

.tool-args-label, .tool-output-label {
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-secondary);
    background: var(--bg-tertiary);
}

.tool-args pre, .tool-output pre {
    margin: 0;
    padding: 12px;
    background: var(--bg-code);
    overflow-x: auto;
    font-size: 12px;
}

.truncation-notice {
    padding: 4px 12px;
    font-size: 11px;
    color: var(--text-secondary);
    background: var(--bg-tertiary);
}

/* Cancel button */
.cancel-stream-btn {
    padding: 6px 12px;
    border: 1px solid var(--error-color);
    border-radius: 4px;
    background: transparent;
    color: var(--error-color);
    cursor: pointer;
    font-size: 12px;
}

.cancel-stream-btn:hover {
    background: var(--error-color);
    color: white;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
```

---

## Implementation Phases

### Phase 1: Backend Event Enhancement
1. Modify `BaseReActAgent.stream()` to yield structured trace events
2. Add `event_type` to `PipelineOutput.metadata`
3. Update `_stream_events_from_output()` to handle new event types

### Phase 2: Database Schema
1. Create `agent_traces` table
2. Add trace creation/update/completion methods to `ChatWrapper`
3. Add trace retrieval endpoint

### Phase 3: Cancellation Support
1. Add `AbortController` support to frontend fetch
2. Add `/api/cancel_stream` endpoint
3. Handle `GeneratorExit` in streaming generator
4. Store partial traces on cancellation

### Phase 4: Frontend Trace UI
1. Add `TraceState` management
2. Implement `handleStreamEvent()` dispatcher
3. Create tool block rendering functions
4. Add collapsible/expandable behavior

### Phase 5: Settings & Polish
1. Add verbose mode toggle to settings panel
2. Implement auto-collapse logic
3. Add trace replay from history
4. CSS polish and animations

---

## Testing Checklist

- [ ] Tool calls display with spinner while running
- [ ] Tool output updates in real-time
- [ ] Tool completion shows checkmark/error + duration
- [ ] Verbose mode expands all by default
- [ ] Normal mode collapses after N tools
- [ ] Minimal mode hides all tool blocks
- [ ] Cancel button stops stream immediately
- [ ] Cancelled traces stored with partial data
- [ ] Traces can be retrieved and replayed
- [ ] Settings persist across sessions
- [ ] Long tool outputs truncated with notice
- [ ] Multiple concurrent tool calls display correctly
- [ ] Error states handled gracefully

---

## Open Questions

1. **Thinking events**: Does the current LangGraph stream expose intermediate reasoning? May need custom callback handler.

2. **Tool output storage**: Full output or truncated in `agent_traces.events`? Full could get large.

3. **Replay UI**: Should historical messages show trace on click, or always collapsed?

4. **Token counting**: Should we track token usage per tool call for cost analysis?

---

## Dependencies

- LangGraph streaming with `stream_mode="messages"`
- PostgreSQL with JSONB support
- AbortController API (modern browsers)
- Existing SSE streaming infrastructure
