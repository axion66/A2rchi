---
id: interfaces-chat-utils
title: Chat App Utilities
version: 1.0.0
status: extracted
sources:
  - src/interfaces/chat_app/utils.py
  - src/interfaces/chat_app/document_utils.py
---

# Chat App Utilities

Utility functions for the chat application.

## History Processing

### `collapse_assistant_sequences(history_rows, sender_name=None, sender_index=0) -> List`

Keep only the latest assistant response within any contiguous block.

**Contract:**
- PRE: `history_rows` is list of tuples/rows
- PRE: `sender_index` indicates which tuple element contains sender name
- POST: Contiguous assistant messages collapsed to last one
- POST: Non-assistant messages preserved
- POST: Order maintained

**Example:**
```python
history = [
    ("User", "Hello"),
    ("A2rchi", "Response 1"),
    ("A2rchi", "Response 2"),  # Collapsed
    ("User", "Follow up"),
    ("A2rchi", "Response 3"),
]
collapsed = collapse_assistant_sequences(history, sender_name="A2rchi")
# Result: [("User", "Hello"), ("A2rchi", "Response 2"), ("User", "Follow up"), ("A2rchi", "Response 3")]
```

---

## File Hashing

### `simple_hash(input_string: str) -> str`

Generate MD5 hash of input string.

**Contract:**
- PRE: `input_string` is non-empty string
- POST: Returns decimal string representation of MD5 hash

### `file_hash(filename: str) -> str`

Generate hash-based filename preserving extension.

**Contract:**
- PRE: `filename` contains at least one `.`
- POST: Returns `{hash[:12]}.{extension}`
- POST: Hash derived from original filename

**Example:**
```python
file_hash("document.pdf")  # "123456789012.pdf"
```

---

## File Upload

### `add_uploaded_file(target_dir: str, file, file_extension: str) -> ScrapedResource`

Save uploaded file and create resource for indexing.

**Contract:**
- PRE: `file` is Flask file upload object
- PRE: `target_dir` exists
- POST: File saved with hashed filename
- POST: Returns `ScrapedResource` with metadata

**Returns:**
```python
ScrapedResource(
    url=file.filename,           # Original filename
    content=file_content,        # Raw bytes
    suffix=file_extension,
    source_type="files",
    metadata={
        "content_type": "...",
        "title": file.filename
    }
)
```

---

## File Lookup

### `get_filename_from_hash(hash_string: str, data_path: str, filehashes_yaml_file: str = "manual_file_hashes.yaml") -> Optional[str]`

Look up original filename from hash.

**Contract:**
- POST: Returns original filename if found in YAML mapping
- POST: Returns `None` if not found
- POST: Handles missing YAML file gracefully

---

## Source Management

### `remove_url_from_sources(url: str, sources_path: str) -> None`

Remove a URL from the persistence layer.

**Contract:**
- POST: All documents with matching URL metadata deleted
- POST: Uses `PersistenceService.delete_by_metadata_filter`

---

## Account Management

### `add_username_password(username: str, password: str, salt: str, accounts_path: str, file_name: str = "accounts.yaml") -> None`

Add new user credentials to accounts file.

**Contract:**
- PRE: `salt` is secret string for password hashing
- POST: Password hashed as `simple_hash(password + salt)`
- POST: Credentials saved to YAML file
- POST: If username exists, no action taken (logs warning)

**YAML Format:**
```yaml
username1: "hashed_password_1"
username2: "hashed_password_2"
```

### `check_credentials(username: str, password: str, salt: str, accounts_path: str, file_name: str = 'accounts.yaml') -> bool`

Validate user credentials.

**Contract:**
- POST: Hashes `password + salt` using `simple_hash`
- POST: Returns `True` if hash matches stored hash for username
- POST: Returns `False` otherwise

---

## Security Notes

- Passwords are hashed with MD5 + salt (legacy, consider upgrading)
- Salt should be stored as environment variable
- YAML file should have restricted permissions
