---
id: bin-services
title: Service Entry Points
version: 1.0.0
status: extracted
sources:
  - src/bin/service_chat.py
  - src/bin/service_grader.py
  - src/bin/service_piazza.py
  - src/bin/service_mattermost.py
  - src/bin/service_mailbox.py
  - src/bin/service_redmine.py
  - src/bin/service_benchmark.py
  - src/bin/service_create_account.py
  - src/bin/service_uploader.py
---

# Service Entry Points

Entry point scripts for running A2rchi services in containers.

## Common Patterns

All services follow a similar initialization pattern:

```python
#!/bin/python
import os
from src.utils.env import read_secret
from src.utils.logging import setup_logging

# 1. Setup logging
setup_logging()

# 2. Load API keys into environment
os.environ['ANTHROPIC_API_KEY'] = read_secret("ANTHROPIC_API_KEY")
os.environ['OPENAI_API_KEY'] = read_secret("OPENAI_API_KEY")
os.environ['HUGGING_FACE_HUB_TOKEN'] = read_secret("HUGGING_FACE_HUB_TOKEN")

# 3. Load config
config = load_config()

# 4. Initialize and run service
```

---

## Flask Services

### `service_chat.py`

Chat application entry point.

```python
def main():
    # Generate script.js from template with config values
    generate_script(chat_config, a2rchi_config)
    
    # Create and run Flask app
    app = FlaskAppWrapper(Flask(...))
    app.run(debug=True, use_reloader=False, port=port, host=host)
```

**Config:** `config["services"]["chat_app"]`

**Required Secrets:**
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `HUGGING_FACE_HUB_TOKEN`

**Helper Function:**
#### `generate_script(chat_config, a2rchi_config) -> None`
Generate JavaScript from template with config values.

**Contract:**
- POST: Replaces `XX-NUM-RESPONSES-XX` with feedback interval
- POST: Replaces `XX-TRAINED_ON-XX` with agent description
- POST: Writes to `script.js`

---

### `service_grader.py`

Grader application entry point.

```python
app = FlaskAppWrapper(Flask(...))
app.run(debug=debug_mode, use_reloader=False, port=port, host=host)
```

**Config:** `config["services"]["grader_app"]`

**Required Secrets:**
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `HUGGING_FACE_HUB_TOKEN`

---

### `service_uploader.py`

Document uploader service entry point.

**Config:** `config["services"]["uploader"]`

---

## Polling Services

### `service_piazza.py`

Piazza question monitoring service.

```python
piazza_agent = piazza.Piazza()
while True:
    piazza_agent.process_posts()
    time.sleep(update_time)
```

**Config:** `config["utils"]["piazza"]`
- `update_time` - Polling interval in seconds

**Required Secrets:**
- `PIAZZA_EMAIL`
- `PIAZZA_PASSWORD`
- `SLACK_WEBHOOK`
- LLM API keys

**Startup Delay:** 30 seconds (to stagger DataManager initialization)

---

### `service_mattermost.py`

Mattermost message monitoring service.

```python
mattermost_agent = mattermost.Mattermost()
while True:
    mattermost_agent.process_posts()
    time.sleep(update_time)
```

**Config:** `config["utils"]["mattermost"]`
- `update_time` - Polling interval in seconds

**Required Secrets:**
- `MATTERMOST_WEBHOOK`
- `MATTERMOST_CHANNEL_ID_READ`
- `MATTERMOST_CHANNEL_ID_WRITE`
- `MATTERMOST_PAK`
- LLM API keys

---

### `service_mailbox.py`

IMAP email monitoring service.

```python
redmine = redmine.Redmine('Redmine_Helpdesk_Mail')  # No A2rchi init
while True:
    mail = mailbox.Mailbox(user=user, password=password)
    mail.process_messages(redmine)
    time.sleep(update_time)
```

**Config:** `config["services"]["redmine_mailbox"]`
- `mailbox_update_time` - Polling interval in seconds

**Required Secrets:**
- `IMAP_USER`
- `IMAP_PW`
- LLM API keys

**Startup Delay:** 60 seconds

**Note:** Creates Redmine with name `'Redmine_Helpdesk_Mail'` which skips A2rchi initialization.

---

### `service_redmine.py`

Redmine ticket monitoring service.

```python
redmine = redmine.Redmine('Redmine_Helpdesk')
while True:
    redmine.load()
    redmine.process_new_issues()
    redmine.process_resolved_issues()
    time.sleep(update_time)
```

**Config:** `config["services"]["redmine_mailbox"]`
- `redmine_update_time` - Polling interval in seconds

**Required Secrets:**
- `REDMINE_USER`
- `REDMINE_PW`
- LLM API keys

**Startup Delay:** 30 seconds

---

## Utility Services

### `service_create_account.py`

Interactive account creation utility.

**Purpose:** Create user accounts for chat app authentication.

---

### `service_benchmark.py`

Benchmarking and evaluation service.

```python
class ResultHandler:
    results: List = []  # Store results per config
    metadata: Dict = {}  # Benchmark run metadata
    
    @staticmethod
    def map_prompts(config: Dict) -> None
    
    @staticmethod
    def handle_results(config_path: Path, results: Dict, total_results: Dict) -> None
```

**Config:** Loaded from `/root/A2rchi/config.yaml`

**Output:** `/root/A2rchi/benchmarks/`

**Dependencies:**
- RAGAS for evaluation metrics
- LangChain for LLM/embedding wrappers

**Metrics:**
- `answer_relevancy`
- `context_precision`
- `context_recall`
- `faithfulness`

**Required Secrets:**
- `OPENAI_API_KEY` (for RAGAS evaluation)
- `ANTHROPIC_API_KEY`
- `HUGGING_FACE_HUB_TOKEN`

---

## Multiprocessing

Services using multiprocessing (e.g., `service_chat.py`):

```python
if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
```

This ensures proper process spawning on all platforms.

---

## Startup Coordination

Services use `time.sleep()` at startup to stagger DataManager initialization:
- `service_piazza.py` - 30 second delay
- `service_redmine.py` - 30 second delay  
- `service_mailbox.py` - 60 second delay

This prevents concurrent vectorstore updates during container startup.

**Future Improvement:** Replace with proper synchronization mechanism.
