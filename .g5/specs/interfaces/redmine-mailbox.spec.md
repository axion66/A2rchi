---
id: interfaces-redmine-mailbox
title: Redmine-Mailbox Integration
version: 1.0.0
status: extracted
sources:
  - src/interfaces/redmine_mailer_integration/mailbox.py
  - src/interfaces/redmine_mailer_integration/redmine.py
---

# Redmine-Mailbox Integration

Integration for processing support emails and creating/updating Redmine tickets with AI-generated responses.

## Mailbox

IMAP mailbox handler for processing incoming support emails.

```python
class Mailbox:
    def __init__(self, user: str, password: str):
        self.mailbox: imaplib.IMAP4_SSL
        self.user: str
        self.password: str
        self.config: Dict  # From services.redmine_mailbox
```

### Methods

#### `process_messages(redmine: Redmine) -> None`
Process all messages in the mailbox.

**Contract:**
- POST: All messages in inbox processed
- POST: New issues created or existing reopened
- POST: Processed messages deleted
- POST: Mailbox closed and logged out

#### `process_message(num: bytes, redmine: Redmine) -> None`
Process a single email message.

**Contract:**
- POST: If `ISSUE_ID:` found in body, issue reopened with note
- POST: If no issue ID, new issue created
- POST: Attachments uploaded to Redmine
- POST: Temporary attachment files cleaned up

### Private Methods

#### `_find_issue_id(description: str) -> int`
Extract Redmine issue ID from email body.

**Contract:**
- POST: Returns issue ID if `ISSUE_ID:` pattern found
- POST: Returns 0 if not found

#### `_get_attachments(msg: email.message.Message) -> List[Dict]`
Extract attachments from email.

**Contract:**
- POST: Returns list of `{"path": str, "filename": str}`
- POST: Attachments saved to `/tmp/`

#### `_get_fields(msg: email.message.Message) -> Tuple[str, str, str, str]`
Extract sender, CC, subject, and body from email.

#### `_get_email_body(msg: email.message.Message) -> str`
Extract and decode email body.

**Contract:**
- POST: Handles multipart and HTML emails
- POST: HTML converted to plain text via BeautifulSoup

#### `_verify() -> bool`
Verify IMAP connection credentials.

#### `_connect() -> imaplib.IMAP4_SSL`
Establish IMAP connection.

---

## RedmineAIWrapper

Wrapper for generating AI responses to Redmine ticket questions.

```python
class RedmineAIWrapper:
    def __init__(self):
        self.data_manager: DataManager
        self.config: Dict
        self.a2rchi: A2rchi  # Using configured pipeline (e.g., CMSCompOpsAgent)
        self.pg_config: Dict
        self.config_id: int
```

### Methods

#### `__call__(history: List[Tuple[str, str]], issue_id: int) -> str`
Generate AI response for ticket conversation.

**Contract:**
- PRE: `history` contains message tuples
- POST: Returns AI-generated answer
- POST: Conversation stored in PostgreSQL
- POST: Vectorstore updated before query

**History Processing:**
- Messages with `ISSUE_ID:` marked as Expert
- Last message marked as User (current question)
- Earlier messages marked as A2rchi

#### `prepare_context_for_storage(source_documents: List) -> Tuple[str, str]`
Format retrieved documents for database storage.

**Contract:**
- POST: Returns (primary_link, formatted_context)

#### `insert_conversation(issue_id: int, user_message: str, a2rchi_message: str, link: str, context: str, ts: datetime) -> None`
Store conversation in PostgreSQL.

### Static Methods

#### `get_substring_between(text: str, start_word: str, end_word: str) -> str`
Extract text between markers.

---

## Redmine

Main class for Redmine API integration.

```python
class Redmine:
    def __init__(self, name: str):
        self.config: Dict
        self.data_manager: DataManager
        self.ai_wrapper: RedmineAIWrapper
        self.redmine: RedmineClient  # From redminelib
        self.project_id: int
```

### Methods

#### `new_issue(sender: str, cc: str, subject: str, description: str, attachments: List[Dict]) -> int`
Create a new Redmine issue.

**Contract:**
- PRE: Valid sender email
- POST: Issue created in configured project
- POST: Attachments uploaded
- POST: AI response added as note
- POST: Returns issue ID (or 0 on failure)

#### `reopen_issue(issue_id: int, note: str, attachments: List[Dict]) -> None`
Reopen and update existing issue.

**Contract:**
- PRE: `issue_id` is valid
- POST: Issue status set to "open" (ID=1)
- POST: Note added with new message and AI response
- POST: Attachments uploaded

#### `update_issue(issue_id: int, status_id: int = None, note: str = None) -> None`
Update issue status or add note.

#### `get_issue_history(issue_id: int) -> List[Tuple[str, str]]`
Retrieve issue conversation history.

**Contract:**
- POST: Returns list of (sender, content) tuples
- POST: Includes initial description and all notes

### Required Secrets

- `REDMINE_USER` - Redmine API username
- `REDMINE_PW` - Redmine API password/key

### Configuration

From `config["services"]["redmine_mailbox"]`:
- `url` - Redmine base URL
- `project_id` - Default project for new issues
- `pipeline` - A2rchi pipeline name

---

## Integration Flow

1. **Mailbox polls** for new emails
2. For each email:
   - Extract sender, subject, body, attachments
   - Check for existing issue ID in body
3. **If new issue:**
   - Create Redmine issue
   - Generate AI response
   - Add response as note
4. **If existing issue:**
   - Reopen issue
   - Retrieve conversation history
   - Generate AI response with context
   - Add response as note
5. **Cleanup:**
   - Delete processed email
   - Remove temp attachment files

---

## Constants

```python
A2RCHI_PATTERN = '-- A2rchi --'  # Marker for AI responses
ISSUE_ID_OFFSET = 9  # Offset after "ISSUE_ID:" to find number
```
