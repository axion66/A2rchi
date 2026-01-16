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
class TicketResource(BaseResource):
    """Resource representing a ticket from a tracking system."""
    
    ticket_id: str
    title: str
    description: str
    source_system: str  # "redmine", "jira", etc.
    status: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    comments: List[str]
```

**Methods:**

##### `get_hash`
```python
def get_hash(self) -> str
```
Return hash based on `{source_system}:{ticket_id}`.

##### `get_filename`
```python
def get_filename(self) -> str
```
Return `{source_system}_{ticket_id}.txt`.

##### `get_content`
```python
def get_content(self) -> str
```
Return formatted ticket text with title, description, comments.

##### `get_metadata`
```python
def get_metadata(self) -> ResourceMetadata
```
Return metadata with source, dates, status.

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
