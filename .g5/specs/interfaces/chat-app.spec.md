---
id: interfaces-chat-app
title: Chat App Interface
version: 2.0.0
status: active
sources:
  - src/interfaces/chat_app/app.py
  - src/interfaces/chat_app/static/chat.js
  - src/interfaces/chat_app/static/chat.css
---

# Chat App Interface

Flask-based web application for interactive chat with A2rchi. The frontend is a custom vanilla JavaScript application styled to match professional AI assistant interfaces (ChatGPT, Claude).

## Frontend Stack

- **UI**: Custom vanilla JavaScript (no framework dependencies)
- **Styling**: Custom CSS with CSS variables for theming
- **Markdown**: marked.js for markdown-to-HTML conversion
- **Syntax highlighting**: highlight.js for code blocks
- **Streaming**: NDJSON streaming with incremental rendering

## UI Requirements

1. **Streaming**: Render partial responses incrementally as chunks arrive.
2. **Markdown + code**: Render markdown with syntax-highlighted code blocks with copy button.
3. **Chat sessions**: Show conversation list in a collapsible left sidebar.
4. **Model selector**: Dropdown selector in the header for available configs.
5. **A/B testing**: Toggle to show two responses side-by-side or stacked, labeled by model.

## Visual Design System

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│ [≡]  A2rchi                    [Model ▼] [A/B ☐] [Model B ▼]│  ← Header (56px)
├────────────┬────────────────────────────────────────────────┤
│            │                                                │
│  Sidebar   │              Message Area                      │
│  (260px)   │         (centered, max 768px)                  │
│            │                                                │
│ + New Chat │  ┌─────────────────────────────────────────┐   │
│            │  │ 👤 User message                         │   │
│ Today      │  └─────────────────────────────────────────┘   │
│  • Chat 1  │                                                │
│  • Chat 2  │  ┌─────────────────────────────────────────┐   │
│            │  │ 🤖 Assistant response with markdown     │   │
│ Yesterday  │  │    ```python                            │   │
│  • Chat 3  │  │    def hello(): ...                     │   │
│            │  │    ```                                  │   │
│            │  └─────────────────────────────────────────┘   │
│            │                                                │
├────────────┴────────────────────────────────────────────────┤
│    [ Type your message...                        ] [Send]   │  ← Input (72px)
└─────────────────────────────────────────────────────────────┘
```

### Color Palette (Light Theme)

```css
--bg-primary: #ffffff;        /* Main background */
--bg-secondary: #f9fafb;      /* Sidebar, code blocks */
--bg-tertiary: #f3f4f6;       /* Hover states */
--text-primary: #111827;      /* Main text */
--text-secondary: #6b7280;    /* Muted text */
--border-color: #e5e7eb;      /* Borders */
--accent-color: #10a37f;      /* Brand accent (A2rchi green) */
--user-bg: #f3f4f6;           /* User message background */
--assistant-bg: #ffffff;      /* Assistant message background */
--code-bg: #1e1e1e;           /* Code block background (dark) */
```

### Typography

- **Font family**: `Inter, -apple-system, BlinkMacSystemFont, sans-serif`
- **Base size**: 15px for messages, 14px for UI elements
- **Line height**: 1.6 for messages, 1.4 for UI
- **Code font**: `'JetBrains Mono', 'SF Mono', Consolas, monospace`

### Message Styling

- Messages are NOT in bubbles - they use full-width rows with subtle background differentiation
- User messages: Light gray background (#f7f7f8)
- Assistant messages: White background
- Role indicator: Small avatar or icon + name label above message
- Max content width: 768px, centered in viewport
- Code blocks: Dark theme with language label and copy button

### Spacing

- Message vertical padding: 24px
- Message horizontal padding: 16px (content centered with max-width)
- Between messages: 0px (messages are adjacent rows)
- Code block padding: 16px
- Sidebar item padding: 12px 16px

## Streaming Architecture

```
Backend (Flask)                    Frontend (Vanilla JS)
─────────────────                  ────────────────────
stream_mode="messages"      →      Receives raw markdown chunks
  ↓                                      ↓
Yields NDJSON events         →      marked.js renders markdown
  ↓                                      ↓
No server-side rendering     →      highlight.js syntax highlights
```

### Stream Event Types

```json
// Text chunk (token-by-token streaming)
{"type": "chunk", "content": "partial markdown", "conversation_id": "..."}

// Tool invocation
{"type": "step", "step_type": "tool_call", "tool_name": "...", "tool_args": {...}}

// Tool result  
{"type": "step", "step_type": "tool_result", "tool_name": "...", "result": "..."}

// Final response
{"type": "final", "response": "Full markdown response", "msg_id": "...", "sources": "..."}
```

### Client-Side Rendering

The frontend renders markdown using:
- `marked.js` - Markdown to HTML conversion
- `highlight.js` - Syntax highlighting for code blocks

**Contracts:**
- ENSURES: Text chunks rendered incrementally as they arrive
- ENSURES: Code blocks highlighted when complete (closing ```)
- ENSURES: No visual jump between streaming and final state
- ENSURES: All responses stored as raw markdown in database

---

## A/B Response Rendering

When A/B testing is enabled, each user prompt yields two assistant responses.

**Contracts:**
- PRE: A/B mode is enabled in UI configuration
- POST: Two assistant messages are rendered per user prompt
- POST: Each response is labeled with its model/config name (Model A / Model B)
- POST: Responses are grouped together (stacked by default)

---

## Model Selector

The model selector maps to existing `config_name` values returned by `/configs`.

**Contracts:**
- PRE: `/configs` returns a list of available configs
- POST: Selecting a config updates the active config for subsequent requests

---

## Conversation Sidebar

The left sidebar lists existing chat sessions and supports creating new ones.

**Contracts:**
- POST: Conversation list is populated from `/conversations`
- POST: Selecting a conversation loads its history
- POST: Deleting a conversation removes it from the list and storage

---

## AnswerRenderer (Deprecated)

> **Note:** Server-side rendering is deprecated for streaming responses.
> Kept for backward compatibility with non-streaming endpoints.

Custom Markdown renderer with syntax highlighting for code blocks.

```python
class AnswerRenderer(mt.HTMLRenderer):
    """Mistune HTML renderer with custom code block handling"""
    
    RENDERING_LEXER_MAPPING = {
        "python": PythonLexer,
        "java": JavaLexer,
        "javascript": JavascriptLexer,
        "bash": BashLexer,
        # ... more lexers
    }
```

### Methods

#### `block_code(code: str, info: str = None) -> str`
Render fenced code blocks with syntax highlighting.

**Contract:**
- PRE: `code` is string content
- POST: Returns HTML with Pygments highlighting
- POST: Unknown languages default to bash
- POST: Includes copy button if configured

#### `codespan(text: str) -> str`
Render inline code snippets.

**Contract:**
- POST: Returns `<code class="code-snippet">` wrapped text

---

## ConversationAccessError

```python
class ConversationAccessError(Exception):
    """Raised when a client attempts to access a conversation it does not own."""
    pass
```

---

## ChatWrapper

Main wrapper holding chatbot functionality.

```python
class ChatWrapper:
    def __init__(self):
        self.config: Dict
        self.data_manager: DataManager
        self.pg_config: Dict
        self.conn: Optional[psycopg2.connection]
        self.cursor: Optional[psycopg2.cursor]
        self.lock: Lock
        self.a2rchi: A2rchi
        self.number_of_queries: int
        
        # Config tracking
        self.default_config_name: str
        self.current_config_name: Optional[str]
        self.config_id: Optional[int]
        self.config_name_to_id: Dict[str, int]
        self._config_cache: Dict[str, Dict]
```

### Methods

#### `__call__(history: List[Tuple[str, str]], conversation_id: str) -> Tuple[str, str, str, List]`
Execute chat query and return response.

**Contract:**
- PRE: `history` is list of (sender, message) tuples
- PRE: `conversation_id` is valid UUID
- POST: Returns (user_message, answer, sources_html, timings)
- POST: Response stored in PostgreSQL
- POST: Lock acquired during execution
- INV: `number_of_queries < QUERY_LIMIT` per conversation

#### `update_config(config_name: str) -> None`
Switch to a different configuration.

**Contract:**
- PRE: `config_name` exists in available configs
- POST: `current_config_name` updated
- POST: `a2rchi` reinitialized with new config
- POST: `data_manager` re-runs vectorstore update

#### `get_conversation_history(conversation_id: str, client_id: str) -> List[Dict]`
Retrieve conversation history for display.

**Contract:**
- PRE: `conversation_id` and `client_id` are valid
- POST: Returns list of message dicts with feedback
- RAISES: `ConversationAccessError` if client doesn't own conversation

#### `create_conversation(client_id: str, title: str = None) -> str`
Create new conversation.

**Contract:**
- POST: Returns new conversation UUID
- POST: Row inserted into conversations table

#### `delete_conversation(conversation_id: str, client_id: str) -> None`
Delete a conversation.

**Contract:**
- PRE: Client owns conversation
- POST: Conversation and messages removed from database
- RAISES: `ConversationAccessError` if unauthorized

#### `submit_feedback(conversation_id: str, msg_id: str, rating: int, text: str) -> None`
Submit feedback for a message.

**Contract:**
- PRE: `rating` is valid feedback value
- POST: Feedback stored in database

#### `upload_file(file, conversation_id: str) -> ScrapedResource`
Handle file upload for RAG.

**Contract:**
- PRE: File has valid extension
- POST: File saved to data directory
- POST: Returns `ScrapedResource` for indexing

---

## Flask Application

### Routes

#### `GET /`
Render main chat interface.

#### `POST /chat`
Submit chat query.

**Request:**
```json
{
  "history": [["User", "message"], ...],
  "conversation_id": "uuid"
}
```

**Response:**
```json
{
  "answer": "rendered_html",
  "sources": "sources_html",
  "msg_id": "uuid"
}
```

#### `GET /conversations`
List user's conversations.

#### `POST /conversations`
Create new conversation.

#### `DELETE /conversations/<id>`
Delete conversation.

#### `POST /feedback`
Submit message feedback.

#### `POST /upload`
Upload document for RAG.

#### `GET /configs`
List available configurations.

#### `POST /configs/<name>`
Switch to configuration.

### Authentication

Supports optional OAuth (SSO) when configured:
- `GET /login` - Initiate OAuth flow
- `GET /authorize` - OAuth callback
- `GET /logout` - Clear session

### Session Management

- `client_id` - Anonymous or authenticated user ID
- `config_name` - Active configuration name
- Session stored server-side

---

## Constants

```python
QUERY_LIMIT = 10000  # Max queries per conversation
A2RCHI_SENDER = "A2rchi"
```

## Configuration

From `config["services"]["chat_app"]`:
- `pipeline` - Pipeline name for A2rchi
- `include_copy_button` - Show copy button in code blocks
- OAuth settings (optional)
