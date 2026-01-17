---
spec_id: bin
type: module
status: extracted
children:
  - bin/services
---

# Bin Module

Service entry points for A2rchi applications. Each script is a standalone runner.

## Services

| Script | Service | Description |
|--------|---------|-------------|
| `service_chat.py` | Chat | Web chat interface |
| `service_grader.py` | Grader | AI grading interface |
| `service_uploader.py` | Uploader | Document upload service |
| `service_benchmark.py` | Benchmark | RAG benchmarking |
| `service_mattermost.py` | Mattermost | Chat bot |
| `service_piazza.py` | Piazza | Q&A bot |
| `service_mailbox.py` | Mailbox | Email integration |
| `service_redmine.py` | Redmine | Ticket integration |
| `service_create_account.py` | Accounts | User management |

## Entry Point Pattern

```python
# service_*.py
from src.interfaces.some_app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
```

## Docker Usage

Each service maps to a Docker container:

```yaml
services:
  chat:
    command: python src/bin/service_chat.py
  grader:
    command: python src/bin/service_grader.py
```
