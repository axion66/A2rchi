---
id: interfaces-integrations
title: Platform Integrations
version: 1.0.0
status: extracted
sources:
  - src/interfaces/piazza.py
  - src/interfaces/mattermost.py
---

# Platform Integrations

Integration wrappers for external platforms (Piazza, Mattermost).

## PiazzaAIWrapper

Wrapper for answering Piazza questions using A2rchi.

```python
class PiazzaAIWrapper:
    def __init__(self):
        self.data_manager: DataManager
        self.a2rchi: A2rchi  # Using QAPipeline
```

### Methods

#### `__call__(post: Dict) -> Tuple[str, str]`
Generate answer for a Piazza post.

**Contract:**
- PRE: `post` contains `history` with `subject` and `content`
- POST: Returns (answer, formatted_question)
- POST: Vectorstore updated before query

**Post Format:**
```python
post = {
    "history": [{
        "subject": "Question title",
        "content": "Question body"
    }],
    "nr": 123  # Post number
}
```

---

## Piazza

Main class for processing Piazza feed and generating responses.

```python
class Piazza:
    def __init__(self):
        self.piazza: PiazzaAPI  # From piazza_api library
        self.piazza_net: Network  # Connected network
        self.slack_url: str  # Webhook for posting responses
        self.min_next_post_nr: int  # Track processed posts
        self.ai_wrapper: PiazzaAIWrapper
```

### Methods

#### `process_posts() -> None`
Process all new posts since last run.

**Contract:**
- POST: All posts with `nr >= min_next_post_nr` processed
- POST: Responses sent to Slack webhook
- POST: `min_next_post_nr` updated to `max(processed) + 1`
- POST: State persisted to `min_next_post.json`

#### `write_min_next_post(min_next_post_nr: int) -> None`
Persist post tracking state.

**Contract:**
- POST: State saved to JSON file

#### `read_min_next_post() -> int`
Read post tracking state.

**Contract:**
- POST: If file exists, returns stored value
- POST: If file missing, initializes from latest feed post + 1

### Required Secrets

- `PIAZZA_EMAIL` - Piazza account email
- `PIAZZA_PASSWORD` - Piazza account password
- `SLACK_WEBHOOK` - Slack webhook URL for responses

### Configuration

From `config["utils"]["piazza"]`:
- `network_id` - Piazza network/class ID

---

## MattermostAIWrapper

Wrapper for answering Mattermost messages using A2rchi.

```python
class MattermostAIWrapper:
    def __init__(self):
        self.data_manager: DataManager
        self.a2rchi: A2rchi
```

### Methods

#### `__call__(post: Dict) -> Tuple[str, str]`
Generate answer for a Mattermost post.

**Contract:**
- PRE: `post` contains `message` field
- POST: Returns (answer, original_message)
- POST: Vectorstore updated before query

---

## Mattermost

Main class for processing Mattermost channel and responding.

```python
class Mattermost:
    def __init__(self):
        self.mattermost_url: str  # Base URL
        self.mattermost_webhook: str  # Response webhook
        self.mattermost_channel_id_read: str  # Channel to monitor
        self.mattermost_channel_id_write: str  # Channel for responses
        self.PAK: str  # Personal Access Key
        self.mattermost_headers: Dict  # Auth headers
        self.ai_wrapper: MattermostAIWrapper
```

### Methods

#### `process_posts() -> None`
Process latest unanswered post.

**Contract:**
- POST: Latest non-system, non-A2rchi post processed
- POST: Response sent via webhook
- POST: Answered post ID tracked to avoid re-processing

#### `get_last_post() -> Dict`
Get most recent user post.

**Contract:**
- POST: Returns latest post excluding system messages
- POST: Excludes posts from A2rchi bot user

#### `get_active_posts() -> Dict[str, str]`
Get all posts from channel.

**Contract:**
- POST: Returns `{post_id: message}` mapping

#### `filter_posts(posts: Dict, excluded_user_id: str) -> List[Dict]`
Filter out system messages and excluded user.

**Contract:**
- POST: Excludes join/leave/add/remove system messages
- POST: Excludes specified user (typically the bot)

#### `post_response(response: str) -> None`
Send response to Mattermost.

**Contract:**
- POST: Response posted via webhook

#### `checkAnswerExist(tmpID: str) -> bool`
Check if post was already answered.

**Contract:**
- POST: Returns `True` if ID in answered list
- POST: If not answered, adds ID to list

### Required Secrets

- `MATTERMOST_WEBHOOK` - Webhook URL
- `MATTERMOST_CHANNEL_ID_READ` - Source channel
- `MATTERMOST_CHANNEL_ID_WRITE` - Destination channel
- `MATTERMOST_PAK` - Personal Access Key

---

## Service Pattern

Both integrations follow a polling service pattern:
1. Initialize wrappers with data manager and A2rchi
2. Poll for new posts/messages
3. Generate AI response
4. Post response to notification channel (Slack/Mattermost)
5. Track processed items to avoid duplicates
6. Sleep and repeat

Typically run as background services via `service_piazza.py` and `service_mattermost.py`.
