# Design Doc: Streaming Output UI

## Problem

The chat UI currently shows:
1. Tool calls/results streaming (works ✅)
2. Final LLM response arrives **all at once** (no token streaming ❌)

Users see a loading spinner, then the entire response appears. For long responses, this feels slow and unresponsive.

## Goals

1. **Token-level streaming** - Stream LLM response tokens to the UI as they're generated
2. **Continuous markdown rendering** - Render markdown incrementally as tokens arrive (like ChatGPT/Claude)
3. **Syntax highlighting** - Code blocks highlight correctly during and after streaming
4. **No visual jump** - Eliminate the jarring transition from raw text to rendered HTML

## Current Architecture

```
User Query
    │
    ▼
FlaskAppWrapper.get_chat_response_stream()
    │
    ▼
ChatWrapper.stream()
    │
    ▼
A2rchi.stream()
    │
    ▼
BaseAgent.stream()  ← uses stream_mode="updates" (whole messages)
    │
    ▼
LangGraph agent.stream()
    │
    ▼
Backend renders markdown with Mistune + Pygments
    │
    ▼
Frontend receives pre-rendered HTML
```

**Problems:**
1. `stream_mode="updates"` yields complete messages, not tokens
2. Backend renders markdown server-side - can't stream rendered content
3. Frontend shows raw text during stream, then jumps to rendered HTML

## Solution: Client-Side Markdown Rendering

Move markdown rendering from backend (Mistune/Pygments) to frontend (marked.js/highlight.js).

### Architecture After

```
Backend streams raw markdown tokens
    │
    ▼
Frontend receives chunks
    │
    ▼
marked.js renders markdown on each chunk
    │
    ▼
highlight.js highlights code blocks
    │
    ▼
User sees continuously rendered response
```

## Changes Required

### 1. Backend: `base_react.py` - Stream tokens

Use `stream_mode="messages"` to get token-level streaming:

```python
def stream(self, **kwargs) -> Iterator[PipelineOutput]:
    for event in self.agent.stream(inputs, stream_mode="messages"):
        message_chunk, metadata = event
        
        if hasattr(message_chunk, 'content') and message_chunk.content:
            yield PipelineOutput(
                answer=message_chunk.content,  # Raw markdown tokens
                type="chunk",
                final=False,
            )
        
        if hasattr(message_chunk, 'tool_calls') and message_chunk.tool_calls:
            yield PipelineOutput(
                tool_calls=message_chunk.tool_calls,
                type="tool_call", 
                final=False,
            )
    
    # Final output with complete raw markdown
    yield PipelineOutput(answer=full_response, final=True)
```

### 2. Backend: `chat_app/app.py` - Return raw markdown

Remove server-side markdown rendering:

```python
def _finalize_result(self, output, ...):
    # OLD: answer = self.render_answer(output.answer)  # Mistune HTML
    # NEW: 
    answer = output.answer  # Raw markdown
    ...
```

Update `_stream_events_from_output()` to emit chunk events:

```python
def _stream_events_from_output(self, output, ...):
    if getattr(output, 'type', None) == "chunk":
        return [{
            "type": "chunk",
            "content": output.answer,
            "conversation_id": conversation_id,
        }]
    # ... existing tool handling
```

### 3. Frontend: `index.html` - Add highlight.js

```html
<head>
    ...
    <!-- Add highlight.js for code syntax highlighting -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <!-- Already have marked.js -->
    <script src="https://cdn.jsdelivr.net/npm/marked@2.0.3/marked.min.js"></script>
</head>
```

### 4. Frontend: `script.js-template` - Configure marked + render on stream

```javascript
// Configure marked.js with highlight.js
marked.setOptions({
    breaks: true,
    gfm: true,
    highlight: (code, lang) => {
        try {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return hljs.highlightAuto(code).value;
        } catch (e) {
            return code;
        }
    }
});

// Render markdown on each chunk
const applyStreamChunk = (chunk) => {
    streamedText += chunk;
    ensureStreamingParagraph();
    streamingParagraph.innerHTML = marked.parse(streamedText);
    chatContainer.scrollTo(0, chatContainer.scrollHeight);
    return true;
};

// Finalization - content already rendered, just save
const finalizeIncomingChat = (incomingChatDiv, pElement, responseData) => {
    if (responseData && responseData.response !== undefined) {
        // Render final markdown (in case any cleanup needed)
        pElement.innerHTML = marked.parse(responseData.response);
        // ... rest of metadata saving
    }
    // ... rest stays same
};
```

### 5. CSS: Style code blocks to match current look

```css
/* Match Pygments styling with highlight.js */
.chat-details pre {
    background: var(--incoming-chat-code-snippet);
    border-radius: 8px;
    padding: 12px;
    overflow-x: auto;
}

.chat-details pre code {
    font-family: Consolas, Monaco, "Lucida Console", monospace;
    font-size: 0.9rem;
}

.chat-details code:not(pre code) {
    background: var(--incoming-chat-code-snippet);
    padding: 2px 6px;
    border-radius: 4px;
}
```

## Event Flow (After Change)

```
Backend yields:
  {"type": "chunk", "content": "The"}
  {"type": "chunk", "content": " answer"}
  {"type": "chunk", "content": " is"}
  {"type": "step", "step_type": "tool_call", ...}
  {"type": "step", "step_type": "tool_result", ...}
  {"type": "chunk", "content": "Based"}
  {"type": "chunk", "content": " on"}
  ...
  {"type": "final", "response": "The answer is...<full markdown>"}

Frontend on each chunk:
  streamedText += chunk.content
  element.innerHTML = marked.parse(streamedText)  // Re-render
```

## Affected Files

| File | Change |
|------|--------|
| `src/a2rchi/pipelines/agents/base_react.py` | Use `stream_mode="messages"`, yield chunks |
| `src/interfaces/chat_app/app.py` | Remove Mistune rendering, emit chunk events |
| `src/interfaces/chat_app/templates/index.html` | Add highlight.js CDN |
| `src/interfaces/chat_app/static/script.js-template` | Configure marked.js, render on chunk |
| `src/interfaces/chat_app/static/style.css` | Style code blocks for highlight.js |

## Affected Specs

1. **pipelines/agents-tools.spec.md** - Update stream() to document chunk yielding
2. **interfaces/chat-app.spec.md** - Remove AnswerRenderer, document client-side rendering

## Testing

1. Open chat UI
2. Send a query that triggers the agent
3. Verify:
   - Text appears token-by-token with markdown rendering
   - Code blocks highlight correctly as they complete
   - Tool calls still show in collapsible section
   - Inline code renders correctly
   - No visual jump at finalization
   - Conversation history loads correctly (also needs marked.parse)

## Migration Notes

- Remove `AnswerRenderer` class (or keep for non-streaming fallback)
- Existing conversation history in DB contains raw markdown (good) or HTML?
  - If HTML: need migration or detect and passthrough
  - If markdown: just render with marked.js on load

## Non-Goals

- Streaming for classic pipelines (QAPipeline, GradingPipeline) - future work
- Copy button on code blocks - can add with marked.js renderer extension

## Risks

1. **highlight.js vs Pygments styling** - May need CSS tweaks to match
2. **marked.js vs Mistune output** - Minor differences possible, test thoroughly
3. **Partial code blocks** - marked.js handles gracefully (shows raw until closed)
4. **Performance** - Re-parsing full text on each chunk; should be fine for typical response sizes

