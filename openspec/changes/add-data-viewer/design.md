# Design: Data Viewer UI

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Browser)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Chat Page  │  │  Data Page  │  │  Shared Components      │  │
│  │  /chat      │  │  /data      │  │  - Header               │  │
│  │             │◄─┼─►           │  │  - Sidebar (nav)        │  │
│  └─────────────┘  └──────┬──────┘  └─────────────────────────┘  │
│                          │                                       │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Data Viewer Components                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │   │
│  │  │ DocumentList │  │ PreviewPanel │  │   StatsBar     │  │   │
│  │  └──────────────┘  └──────────────┘  └────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Flask Backend (app.py)                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Data API Endpoints                       │ │
│  │  GET  /api/data/documents         - List documents          │ │
│  │  GET  /api/data/documents/:hash   - Get document details    │ │
│  │  GET  /api/data/documents/:hash/content - Get content       │ │
│  │  POST /api/data/documents/:hash/hide    - Soft delete       │ │
│  │  POST /api/data/documents/:hash/restore - Restore           │ │
│  │  GET  /api/data/stats             - Summary statistics      │ │
│  │  POST /api/data/refresh           - Trigger re-sync         │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  CatalogService │  │  VectorStore    │  │   Filesystem    │  │
│  │  (SQLite)       │  │  (ChromaDB)     │  │   (documents)   │  │
│  │  - metadata     │  │  - embeddings   │  │  - raw content  │  │
│  │  - soft_delete  │  │  - doc count    │  │                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema Changes

### Add soft-delete support to CatalogService

```sql
-- Add column to existing resources table
ALTER TABLE resources ADD COLUMN hidden_at TEXT DEFAULT NULL;
ALTER TABLE resources ADD COLUMN hidden_by TEXT DEFAULT NULL;

-- Index for efficient filtering
CREATE INDEX idx_resources_hidden ON resources(hidden_at);
```

## API Design

### GET /api/data/documents
List all documents with optional filtering.

**Query Parameters:**
- `source_type` (optional): Filter by type (local, web, ticket)
- `search` (optional): Full-text search query
- `include_hidden` (optional): Include soft-deleted docs (default: false)
- `limit` (optional): Max results (default: 100)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "documents": [
    {
      "hash": "abc123...",
      "display_name": "CMS Operations Guide",
      "source_type": "local",
      "url": null,
      "size_bytes": 125000,
      "suffix": ".md",
      "ingested_at": "2026-01-20T10:30:00Z",
      "hidden_at": null
    }
  ],
  "total": 156,
  "limit": 100,
  "offset": 0
}
```

### GET /api/data/documents/:hash/content
Get document content for preview.

**Response:**
```json
{
  "hash": "abc123...",
  "display_name": "CMS Operations Guide",
  "content": "# CMS Operations Guide\n\nThis document...",
  "content_type": "text/markdown",
  "size_bytes": 125000,
  "truncated": false
}
```

### POST /api/data/documents/:hash/hide
Soft-delete a document.

**Response:**
```json
{
  "success": true,
  "hash": "abc123...",
  "hidden_at": "2026-01-24T15:30:00Z"
}
```

### POST /api/data/documents/:hash/restore
Restore a soft-deleted document.

**Response:**
```json
{
  "success": true,
  "hash": "abc123...",
  "restored_at": "2026-01-24T15:35:00Z"
}
```

### GET /api/data/stats
Get summary statistics.

**Response:**
```json
{
  "total_documents": 156,
  "hidden_documents": 3,
  "total_size_bytes": 13042000,
  "vectorstore_count": 1250,
  "by_source_type": {
    "local": 42,
    "web": 89,
    "ticket": 25
  },
  "last_sync": "2026-01-24T15:00:00Z"
}
```

## Frontend Components

### 1. DataPage (`/data` route)
Main container component managing:
- Document list state
- Selected document state
- Search/filter state
- Refresh functionality

### 2. StatsBar
Horizontal bar showing:
- Total document count
- Total storage size
- Vectorstore document count
- Last sync timestamp
- Refresh button with loading state

### 3. DocumentList (Left Panel)
Scrollable list with:
- Search input (debounced)
- Source type filter dropdown
- "Show hidden" toggle
- Collapsible groups by source type
- Document items with:
  - Type icon (📄 file, 🌐 web, 🎫 ticket)
  - Display name (truncated)
  - Size
  - Hidden indicator if applicable

### 4. PreviewPanel (Right Panel)
Document details and content:
- Metadata section (source, URL, dates)
- Action buttons (Hide/Restore)
- Content viewer:
  - Markdown rendering for .md files
  - Syntax highlighting for code
  - Plain text for others
  - PDF handling (show metadata + text extract)

## State Management

```javascript
// Data page state
const dataState = {
  // Document list
  documents: [],
  loading: false,
  error: null,
  
  // Filters
  searchQuery: '',
  sourceTypeFilter: 'all',
  includeHidden: false,
  
  // Selection
  selectedHash: null,
  selectedDocument: null,
  contentLoading: false,
  
  // Stats
  stats: null,
  statsLoading: false,
  
  // Actions
  refreshing: false,
};
```

## Navigation Integration

### Option A: Header Link
Add "Data" link next to chat title in header.

```html
<header class="header">
  <div class="header-left">
    <button class="sidebar-toggle">...</button>
    <nav class="header-nav">
      <a href="/chat" class="nav-link active">Chat</a>
      <a href="/data" class="nav-link">Data</a>
    </nav>
  </div>
</header>
```

### Option B: Sidebar Navigation
Add to existing sidebar as a new section.

**Recommendation:** Option A (Header Link) - cleaner, doesn't clutter sidebar.

## Styling Approach

Reuse existing CSS variables and patterns from chat UI:
- Same color scheme (`--bg-primary`, `--text-primary`, etc.)
- Same button/input styles
- Same modal/panel patterns
- Responsive breakpoints

New CSS classes:
- `.data-page` - Main container
- `.data-stats` - Stats bar
- `.data-list` - Document list panel
- `.data-preview` - Preview panel
- `.document-item` - List item
- `.document-group` - Collapsible group

## Error Handling

1. **Network errors** - Show toast notification, allow retry
2. **Document not found** - Clear selection, refresh list
3. **Content too large** - Truncate with "Show full" link
4. **Refresh in progress** - Disable button, show spinner

## Performance Considerations

1. **Pagination** - Load 100 docs at a time, infinite scroll
2. **Debounced search** - 300ms delay before API call
3. **Lazy content loading** - Only fetch content when selected
4. **Content caching** - Cache last N viewed documents
5. **Virtual scrolling** - Consider for very large lists (1000+)
