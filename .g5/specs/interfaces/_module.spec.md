---
spec_id: interfaces
type: module
status: extracted
children:
  - interfaces/chat-app
  - interfaces/chat-utils
  - interfaces/grader-app
  - interfaces/integrations
  - interfaces/redmine-mailbox
---

# Interfaces Module

User-facing applications and integrations for A2rchi.

## Applications

| Interface | Type | Description |
|-----------|------|-------------|
| `chat_app` | Flask web app | Interactive chat UI |
| `grader_app` | Flask web app | AI grading interface |
| `piazza.py` | Bot | Piazza Q&A integration |
| `mattermost.py` | Bot | Mattermost chat bot |
| `redmine_mailer_integration/` | Service | Redmine ticket → email |

## Architecture

```
interfaces/
├── chat_app/
│   ├── app.py              # Flask app + ChatWrapper
│   ├── utils.py            # History processing
│   ├── document_utils.py   # File handling
│   ├── templates/          # Jinja2 HTML
│   └── static/             # CSS/JS
├── grader_app/
│   ├── app.py              # Flask app + GradingWrapper
│   └── templates/
├── piazza.py               # Piazza bot
├── mattermost.py           # Mattermost bot
└── redmine_mailer_integration/
    ├── mailbox.py          # Email fetching
    └── redmine.py          # Redmine API
```

## Chat App

```python
class ChatWrapper:
    """Wraps A2rchi for web chat interface."""
    def __call__(history, conversation_id) -> (answer, sources, msg_id)
    def update_config(config_name) -> None
    def get_conversation_history(conv_id, client_id) -> List[Dict]
```

## Grader App

```python
class GradingWrapper:
    """Wraps A2rchi for grading interface."""
    def __call__(student_solution, rubric, comments) -> feedback

class ImageToTextWrapper:
    """Extracts text from images for grading."""
    def __call__(images: List[str]) -> extracted_text
```

## Bot Protocol

Both Piazza and Mattermost bots follow:

```python
class Bot:
    def __init__(config)
    def run() -> None           # Main loop
    def handle_message(msg)     # Process incoming
    def send_response(answer)   # Reply
```

## Authentication

- Chat app: Optional OAuth/SSO or session-based
- Grader app: Flask-Login with user roles
- Bots: API tokens from config
