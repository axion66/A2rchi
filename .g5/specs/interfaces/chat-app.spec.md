---
id: interfaces-chat-app
title: Chat App Interface
version: 1.0.0
status: extracted
sources:
  - src/interfaces/chat_app/app.py
---

# Chat App Interface

Flask-based web application for interactive chat with A2rchi.

## AnswerRenderer

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
