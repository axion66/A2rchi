---
type: spec
module: data_manager.collectors.tickets
version: "1.0"
status: extracted
test_file: tests/unit/test_tickets.py
source_files:
  - src/data_manager/collectors/tickets/ticket_manager.py
  - src/data_manager/collectors/tickets/ticket_resource.py
---

# Tickets Collector Spec

## Overview

Ticket system integration for collecting issues from Redmine, Jira, and other ticket systems.

## Dependencies

- `src/data_manager/collectors/persistence.PersistenceService`
- `src/data_manager/collectors/tickets/ticket_resource.TicketResource`

## Public API

### Classes

#### `TicketManager`
```python
class TicketManager:
    """Coordinates ticket collection from configured integrations."""
    
    dm_config: Dict
    integrations: List[TicketIntegration]
```

**Constructor:**
```python
def __init__(self, dm_config: Dict[str, Any]) -> None
```

**Contracts:**
- ENSURES: Initializes configured ticket integrations
- ENSURES: Skips disabled integrations

**Methods:**

##### `collect`
```python
def collect(self, persistence: PersistenceService) -> None
```
Collect tickets from all configured integrations.

**Contracts:**
- ENSURES: Iterates all integrations
- ENSURES: Persists each ticket as `TicketResource`

---

#### `TicketResource`
```python
@dataclass
class TicketResource(BaseResource):
    """Standard representation of a collected support ticket."""
    
    ticket_id: str
    content: str
    source_type: str
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Methods:**

##### `get_hash`
```python
def get_hash(self) -> str
```
Return hash as `{source_type}_{normalised_ticket_id}`.

**Contracts:**
- ENSURES: Special characters in ticket_id replaced with underscores

##### `get_filename`
```python
def get_filename(self) -> str
```
Return `{get_hash()}.txt`.

##### `get_content`
```python
def get_content(self) -> str
```
Return the `content` field.

##### `get_metadata`
```python
def get_metadata(self) -> ResourceMetadata
```
Return ResourceMetadata with display_name and extra fields.

**Contracts:**
- ENSURES: `display_name` from metadata dict or defaults to `{source_type}:{ticket_id}`
- ENSURES: Includes ticket_id, source_type, and created_at in extra fields

## Integrations

### RedmineTickets
```python
class RedmineTickets:
    """Fetches tickets from Redmine API."""
    
    base_url: str
    api_key: str
    project_id: Optional[str]
```

### JiraTickets
```python
class JiraTickets:
    """Fetches tickets from Jira API."""
    
    base_url: str
    username: str
    api_token: str
    jql_query: str
```

## Configuration

```yaml
data_manager:
  sources:
    tickets:
      redmine:
        enabled: true
        base_url: "https://redmine.example.com"
        api_key: "${REDMINE_API_KEY}"
        project_id: "myproject"
      jira:
        enabled: false
        base_url: "https://jira.example.com"
        jql_query: "project = PROJ"
```

## Invariants

1. Ticket ID unique within source system
2. Comments concatenated in chronological order
3. Missing fields default to None/empty
