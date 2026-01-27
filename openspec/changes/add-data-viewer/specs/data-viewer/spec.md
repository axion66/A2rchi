# Data Viewer Specification (Per-Chat)

## ADDED Requirements

### Requirement: Document Listing SHALL Display All Documents with Per-Chat State
The system SHALL display a paginated list of all documents in the knowledge base along with their enabled/disabled state for the current chat. Each document entry SHALL show: checkbox, display name, source type icon, and size. Documents SHALL be grouped by source type (Local Files, Web Pages, Tickets). Groups SHALL be collapsible/expandable.

#### Scenario: View document list with per-chat state
- **GIVEN** user navigates to /data for a chat session
- **WHEN** page loads successfully
- **THEN** stats bar shows enabled/total document counts
- **AND** document list shows documents grouped by source type
- **AND** each document shows checkbox indicating enabled state
- **AND** disabled documents are visually distinguished

---

### Requirement: Search SHALL Filter Documents by Name and URL
The system SHALL provide a search input for filtering documents. Search SHALL match against document display name and URL. Search SHALL be debounced (300ms) to reduce API calls. Search SHALL show result count and preserve enabled/disabled state.

#### Scenario: Search filters documents
- **GIVEN** document list is displayed with multiple documents
- **WHEN** user types "operations" in search input
- **THEN** after 300ms debounce delay
- **AND** list filters to show only documents matching "operations"
- **AND** each result shows its enabled/disabled checkbox state

---

### Requirement: Filtering SHALL Support Source Type and Enabled State
The system SHALL provide source type filter (All, Local, Web, Ticket). System SHALL provide filter to show All, Enabled only, or Disabled only documents. Filters SHALL be combinable with search.

#### Scenario: Filter by enabled state
- **GIVEN** document list shows all documents
- **WHEN** user selects "Disabled only" from show filter
- **THEN** only disabled documents for this chat are displayed
- **AND** document count updates

---

### Requirement: Document Preview SHALL Display Content and Metadata
The system SHALL display full metadata when selecting a document. System SHALL fetch and display document content. Markdown files SHALL be rendered as formatted HTML. Large content (>100KB) SHALL be truncated with option to expand.

#### Scenario: Preview document content
- **GIVEN** document list is displayed
- **WHEN** user clicks on a document
- **THEN** preview panel shows document metadata (source, URL, dates)
- **AND** document content is fetched and displayed
- **AND** enable/disable toggle for this chat is visible

---

### Requirement: Disable SHALL Exclude Document from Current Chat
Users SHALL be able to disable any document for the current chat. Disabled documents SHALL be excluded from retrieval for this chat only. Disabling SHALL not require confirmation.

#### Scenario: Disable document for chat
- **GIVEN** document is enabled for current chat
- **WHEN** user unchecks the document checkbox
- **THEN** document is marked disabled for this conversation_id
- **AND** checkbox shows unchecked state
- **AND** enabled count in stats decreases
- **AND** subsequent AI responses will not use this document

---

### Requirement: Enable SHALL Include Document in Current Chat
Users SHALL be able to enable a disabled document for the current chat. Enabling SHALL not require confirmation.

#### Scenario: Enable document for chat
- **GIVEN** document is disabled for current chat
- **WHEN** user checks the document checkbox
- **THEN** document is marked enabled for this conversation_id
- **AND** checkbox shows checked state
- **AND** enabled count in stats increases

---

### Requirement: Bulk Selection SHALL Enable or Disable Multiple Documents
Users SHALL be able to enable or disable multiple documents at once. System SHALL provide "Enable All" and "Disable All" actions for filtered results.

#### Scenario: Disable all filtered documents
- **GIVEN** search filter shows 10 documents
- **WHEN** user clicks "Disable All"
- **THEN** all 10 filtered documents are disabled for this chat
- **AND** stats update to reflect changes

---

### Requirement: Statistics SHALL Show Per-Chat Enabled State
The system SHALL display enabled document count, total document count, total storage size, and last sync timestamp. Statistics SHALL reflect the current chat's document selections.

#### Scenario: View per-chat statistics
- **GIVEN** user navigates to /data for a chat
- **WHEN** page loads
- **THEN** stats bar displays "X/Y enabled" (enabled/total)
- **AND** stats bar displays total storage size
- **AND** stats bar displays last sync timestamp

---

### Requirement: Navigation SHALL Provide Access to Per-Chat Data View
Data viewer SHALL be accessible at `/data` route with current conversation context. Header SHALL provide navigation between Chat and Data views. Current page SHALL be highlighted in navigation.

#### Scenario: Navigate to data view for current chat
- **GIVEN** user is on chat page with conversation_id=abc123
- **WHEN** user clicks "Data" link in header
- **THEN** browser navigates to /data
- **AND** data view loads document state for conversation abc123
- **AND** "Back to Chat" returns to the same conversation

---

### Requirement: Default State SHALL Enable All Documents
New chat sessions SHALL have all documents enabled by default. Users SHALL be able to customize from this default.

#### Scenario: New chat has all documents enabled
- **GIVEN** user starts a new chat conversation
- **WHEN** user navigates to data view
- **THEN** all documents show as enabled (checked)
- **AND** stats show "156/156 enabled"

---

## API Contract

### GET /api/data/documents

**Purpose**: Retrieve paginated list of documents with per-chat enabled state

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| conversation_id | string | Yes | - | Current chat conversation ID |
| source_type | string | No | all | Filter: "local", "web", "ticket", "all" |
| search | string | No | "" | Search query |
| enabled | string | No | all | Filter: "all", "enabled", "disabled" |
| limit | integer | No | 100 | Max results (1-500) |
| offset | integer | No | 0 | Pagination offset |

**Response (200)**:
```json
{
  "documents": [
    {
      "hash": "string (64 chars, SHA-256)",
      "display_name": "string",
      "source_type": "local|web|ticket",
      "url": "string|null",
      "size_bytes": "integer",
      "suffix": "string",
      "ingested_at": "ISO8601 datetime",
      "enabled": "boolean"
    }
  ],
  "total": "integer",
  "enabled_count": "integer",
  "limit": "integer",
  "offset": "integer"
}
```

### GET /api/data/documents/:hash/content

**Purpose**: Retrieve document content for preview

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| hash | string | Document hash (SHA-256) |

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| max_size | integer | No | 100000 | Max content bytes to return |

**Response (200)**:
```json
{
  "hash": "string",
  "display_name": "string",
  "content": "string",
  "content_type": "string (MIME type)",
  "size_bytes": "integer",
  "truncated": "boolean"
}
```

### POST /api/data/documents/:hash/enable

**Purpose**: Enable a document for the current chat

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| hash | string | Document hash (SHA-256) |

**Request Body**:
```json
{
  "conversation_id": "string"
}
```

**Response (200)**:
```json
{
  "success": true,
  "hash": "string",
  "enabled": true
}
```

### POST /api/data/documents/:hash/disable

**Purpose**: Disable a document for the current chat

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| hash | string | Document hash (SHA-256) |

**Request Body**:
```json
{
  "conversation_id": "string"
}
```

**Response (200)**:
```json
{
  "success": true,
  "hash": "string",
  "enabled": false
}
```

### POST /api/data/bulk-enable

**Purpose**: Enable multiple documents for the current chat

**Request Body**:
```json
{
  "conversation_id": "string",
  "hashes": ["string", "string", ...]
}
```

**Response (200)**:
```json
{
  "success": true,
  "enabled_count": "integer"
}
```

### POST /api/data/bulk-disable

**Purpose**: Disable multiple documents for the current chat

**Request Body**:
```json
{
  "conversation_id": "string",
  "hashes": ["string", "string", ...]
}
```

**Response (200)**:
```json
{
  "success": true,
  "disabled_count": "integer"
}
```

### GET /api/data/stats

**Purpose**: Retrieve summary statistics for current chat

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| conversation_id | string | Yes | - | Current chat conversation ID |

**Response (200)**:
```json
{
  "total_documents": "integer",
  "enabled_documents": "integer",
  "disabled_documents": "integer",
  "total_size_bytes": "integer",
  "by_source_type": {
    "local": {"total": "integer", "enabled": "integer"},
    "web": {"total": "integer", "enabled": "integer"},
    "ticket": {"total": "integer", "enabled": "integer"}
  },
  "last_sync": "ISO8601 datetime|null"
}
```

## Data Model

### Per-Chat Document Selection Storage

Document selections are stored per conversation. Options:
1. **Session storage** - In-memory, lost on restart
2. **SQLite table** - Persistent, survives restart

Recommended: SQLite table for persistence

```sql
CREATE TABLE chat_document_selections (
  conversation_id TEXT NOT NULL,
  document_hash TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (conversation_id, document_hash)
);
```

### Invariants

1. All documents are enabled by default for new conversations
2. Selections only stored when explicitly changed from default
3. Disabled documents excluded from retrieval for that conversation only
4. Other conversations are not affected by selection changes
5. Document selections persist across page reloads within same session

## UI Component Hierarchy

```
DataPage
├── Header
│   └── Navigation (Chat | Data)
├── StatsBar
│   ├── EnabledCount ("142/156 enabled")
│   ├── TotalSize
│   ├── LastSync
│   └── RefreshButton
├── ContentArea
│   ├── DocumentListPanel
│   │   ├── SearchInput
│   │   ├── FilterDropdowns (Type, Enabled)
│   │   ├── BulkActions (Enable All, Disable All)
│   │   └── DocumentGroups
│   │       └── DocumentItem (checkbox + info) (×N)
│   └── PreviewPanel
│       ├── MetadataSection
│       ├── EnableToggle
│       └── ContentViewer
└── ToastNotifications
```

## Integration with Chat Retrieval

When the chat retrieves documents for RAG:
1. Get conversation_id from current session
2. Query chat_document_selections for disabled hashes
3. Filter retrieval results to exclude disabled documents
4. Return only enabled documents in context
