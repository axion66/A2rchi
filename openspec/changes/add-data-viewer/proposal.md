# Change: Add Data Viewer UI (Per-Chat)

## Why
Users currently have no visibility into what data has been ingested into A2rchi, making it difficult to understand AI answers, verify document availability, and customize which knowledge sources the assistant uses for different conversations.

## What Changes
- Add `/data` route with per-chat document browsing interface
- Add API endpoints for document listing, content retrieval, and per-chat selection
- Add include/exclude functionality for documents on a per-chat basis
- Add statistics display (document count, storage size, vectorstore count)
- Store per-chat document selections in session/conversation state

## Impact
- Affected specs: data-viewer (new capability)
- Affected code: `src/interfaces/chat_app/`, `src/data_manager/`, `src/a2rchi/`

---

## Summary
Add a dedicated Data Viewer page to the A2rchi chat interface that allows users to browse, search, preview, and **select which documents are available for the current chat session**. Each chat can have its own custom set of enabled/disabled documents, giving users fine-grained control over the AI's knowledge base.

## Goals
1. **Transparency** - Users can see all documents the AI has access to
2. **Per-Chat Control** - Select which documents are included/excluded per conversation
3. **Searchability** - Quick filtering and search across documents
4. **Preview** - View document content without leaving the interface
5. **Live Status** - Real-time view of what's enabled for the current chat

## Non-Goals
- Hard deletion of documents (selection only)
- Document editing within the UI
- Bulk upload interface (use existing data manager)
- Global document hiding (per-chat selection only)

## User Stories

### US1: View Data Sources for Current Chat
As a user, I want to see all documents and their enabled/disabled state for my current chat so I understand what knowledge is available.

### US2: Search Documents
As a user, I want to search/filter documents by name, type, or content so I can quickly find specific information.

### US3: Preview Content
As a user, I want to click on a document and see its content so I can verify what the AI knows.

### US4: Exclude Document from Chat
As a user, I want to disable a document for this chat so the AI won't use it in responses.

### US5: Include Document in Chat
As a user, I want to enable a previously disabled document so the AI can use it again.

### US6: View Statistics
As a user, I want to see summary statistics showing how many documents are enabled vs total for this chat.

## Proposed Solution

### Navigation
- Add "Data" button/link in the chat header
- Clicking opens `/data` route for the current chat
- Shows document selection state for the active conversation

### Page Layout
```
┌─────────────────────────────────────────────────────────────┐
│ ← Back to Chat       Data Sources (Chat #123)   🔄 Refresh  │
├─────────────────────────────────────────────────────────────┤
│ 📊 142/156 enabled │ 12.4 MB │ Last sync: 2 min ago        │
├────────────────────────┬────────────────────────────────────┤
│ 🔍 Search...           │                                    │
│ ─────────────────────  │    Document Preview                │
│ Filter: [All Types ▼]  │                                    │
│ ─────────────────────  │    Select a document to view       │
│ Show: [All ▼]          │    its content                     │
│ ─────────────────────  │                                    │
│ ▼ Local Files (42)     │                                    │
│   ☑ 📄 guide.md   1.2MB│                                    │
│   ☐ 📄 manual.pdf 3.4MB│  ← disabled for this chat          │
│ ▼ Web Pages (89)       │                                    │
│   ☑ 🌐 TWiki - DataOps │                                    │
│ ▼ Tickets (25)         │                                    │
│   ☑ 🎫 GGUS-12345      │                                    │
└────────────────────────┴────────────────────────────────────┘
```

### Key Components
1. **Header** - Navigation, title with chat reference, refresh button
2. **Stats Bar** - Enabled/total count, total size, sync status
3. **Document List** (left panel)
   - Search input
   - Type filter dropdown
   - Show filter (All / Enabled / Disabled)
   - Collapsible groups by source type
   - Document items with **checkbox**, icon, name, size
4. **Preview Panel** (right panel)
   - Document metadata (source, URL, dates)
   - Content preview with syntax highlighting
   - Toggle button (Enable/Disable for this chat)

### Per-Chat State
- Document selections stored per conversation_id
- Default: all documents enabled for new chats
- Selections persist across page reloads within same chat session
- Chat retrieval filters to only enabled documents

### API Endpoints
- `GET /api/data/documents?conversation_id=X` - List documents with enabled state
- `GET /api/data/documents/<hash>/content` - Get document content
- `POST /api/data/documents/<hash>/enable` - Enable for current chat
- `POST /api/data/documents/<hash>/disable` - Disable for current chat
- `POST /api/data/bulk-enable` - Enable multiple documents
- `POST /api/data/bulk-disable` - Disable multiple documents
- `GET /api/data/stats?conversation_id=X` - Get stats for chat

## Alternatives Considered

### A: Global soft-delete only
Rejected - Per-chat selection gives more flexibility. Users may want different documents for different conversations.

### B: Tab in Settings Modal
Rejected - Not enough space for document list and preview.

### C: Sidebar Panel
Rejected - Takes space from chat, complex state management.

## Security Considerations
- All users can view and select data (per requirements)
- Selection only - no document deletion from UI
- Selections are per-chat, not persisted across sessions by default

## Dependencies
- Existing `CatalogService` for document metadata
- Existing vectorstore for document retrieval
- Conversation state storage (existing session mechanism)

## Rollout Plan
1. Implement backend API endpoints with conversation_id support
2. Add per-chat document selection storage
3. Build frontend page with document list and checkboxes
4. Add preview panel
5. Integrate with chat retrieval to filter by enabled docs
6. Test with production data
3. Build frontend page with document list
4. Add preview panel
5. Add search and filtering
6. Test with production data
