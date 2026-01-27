# Tasks: Data Viewer Implementation (Per-Chat)

## Phase 1: Database & Backend Foundation

- [ ] **1.1 Create per-chat document selection table**
  - Create `chat_document_selections` table in SQLite
  - Columns: conversation_id, document_hash, enabled, updated_at
  - Primary key on (conversation_id, document_hash)
  - File: `src/data_manager/collectors/utils/index_utils.py`

- [ ] **1.2 Add selection methods to CatalogService**
  - Add `get_document_selection(conversation_id, hash)` method
  - Add `set_document_enabled(conversation_id, hash, enabled)` method
  - Add `bulk_set_enabled(conversation_id, hashes, enabled)` method
  - Add `get_enabled_hashes(conversation_id)` method for retrieval filtering
  - Add `get_stats(conversation_id)` method for per-chat statistics
  - File: `src/data_manager/collectors/utils/index_utils.py`

- [ ] **1.3 Create DataViewerService**
  - Orchestrate catalog queries with selection state
  - Handle content reading from filesystem
  - Content truncation for large documents
  - File: `src/data_manager/data_viewer_service.py` (new)

## Phase 2: API Endpoints

- [ ] **2.1 Add data API routes to Flask app**
  - `GET /api/data/documents?conversation_id=X` - List with per-chat state
  - `GET /api/data/documents/:hash/content` - Get content
  - `POST /api/data/documents/:hash/enable` - Enable for chat
  - `POST /api/data/documents/:hash/disable` - Disable for chat
  - `POST /api/data/bulk-enable` - Enable multiple
  - `POST /api/data/bulk-disable` - Disable multiple
  - `GET /api/data/stats?conversation_id=X` - Per-chat statistics
  - File: `src/interfaces/chat_app/app.py`

- [ ] **2.2 Add data page route**
  - `GET /data` - Serve data viewer page
  - Pass conversation_id context to template
  - File: `src/interfaces/chat_app/app.py`

- [ ] **2.3 Integrate with chat retrieval**
  - Modify retrieval to filter by enabled documents
  - Get disabled hashes for current conversation
  - Exclude disabled documents from RAG context
  - File: `src/a2rchi/a2rchi.py`

## Phase 3: Frontend - Page Structure

- [ ] **3.1 Create data.html template**
  - Base structure with stats bar, list panel, preview panel
  - Include navigation header with Chat/Data links
  - Include conversation_id in page context
  - File: `src/interfaces/chat_app/templates/data.html` (new)

- [ ] **3.2 Add data.css styles**
  - Stats bar layout (enabled/total format)
  - Split panel layout (list + preview)
  - Document list items with checkboxes
  - Checkbox styling for enabled/disabled
  - Preview panel sections
  - Responsive breakpoints
  - File: `src/interfaces/chat_app/static/data.css` (new)

- [ ] **3.3 Add navigation links**
  - Add "Data" link to chat page header
  - Add "Chat" link to data page header
  - Preserve conversation context in navigation
  - Highlight active page in nav
  - Files: `src/interfaces/chat_app/templates/index.html`, `data.html`

## Phase 4: Frontend - Document List

- [ ] **4.1 Implement document list component**
  - Fetch documents with per-chat state from API
  - Render checkboxes for enabled/disabled state
  - Loading and error states
  - Click checkbox to toggle, click row to preview
  - File: `src/interfaces/chat_app/static/data.js` (new)

- [ ] **4.2 Add search functionality**
  - Search input with debounce
  - Filter documents by search query
  - Show "no results" state
  - Preserve checkbox states during search

- [ ] **4.3 Add source type filter**
  - Dropdown: All, Local Files, Web Pages, Tickets
  - Filter on selection change

- [ ] **4.4 Add enabled state filter**
  - Dropdown: All, Enabled, Disabled
  - Filter documents by per-chat state

- [ ] **4.5 Implement grouping by source type**
  - Collapsible groups with checkboxes
  - Document count per group (enabled/total)
  - Expand/collapse all

- [ ] **4.6 Add bulk actions**
  - "Enable All" button for filtered results
  - "Disable All" button for filtered results
  - Update all checkboxes and stats after bulk action

## Phase 5: Frontend - Preview Panel

- [ ] **5.1 Implement preview panel**
  - Show metadata when document selected
  - Display content with loading state
  - Empty state when nothing selected

- [ ] **5.2 Add content rendering**
  - Markdown rendering for .md files
  - Syntax highlighting for code files
  - Plain text display as fallback
  - Handle truncated content

- [ ] **5.3 Add enable/disable toggle**
  - Toggle switch showing enabled state for this chat
  - Update document list checkbox when toggled
  - No confirmation needed

## Phase 6: Stats & Integration

- [ ] **6.1 Implement per-chat stats bar**
  - Fetch and display statistics for conversation
  - "X/Y enabled" format
  - Total size, last sync timestamp

- [ ] **6.2 Add refresh functionality**
  - Refresh button with loading state
  - Re-fetch document list and stats
  - Preserve selections during refresh

- [ ] **6.3 Verify retrieval filtering**
  - Test that disabled documents are excluded from chat
  - Verify AI responses don't include disabled content

## Phase 7: Polish & Testing

- [ ] **7.1 Add loading states**
  - Skeleton loaders for document list
  - Spinner for content loading
  - Disabled states during API calls

- [ ] **7.2 Add error handling**
  - Toast notifications for errors
  - Retry mechanisms
  - Graceful degradation

- [ ] **7.3 Responsive design**
  - Mobile-friendly layout
  - Collapsible preview panel on small screens
  - Touch-friendly checkboxes

- [ ] **7.4 Manual testing**
  - Test enable/disable operations
  - Test with large documents
  - Test with many documents
  - Test that selections persist in same chat
  - Test that different chats have independent selections

## Dependencies

- Tasks in later phases depend on earlier phases
- Phase 3-6 frontend work can proceed in parallel after Phase 2 APIs exist
- Phase 7 should be done last

## Estimated Effort

- Phase 1: 3-4 hours
- Phase 2: 3-4 hours  
- Phase 3: 2-3 hours
- Phase 4: 4-5 hours
- Phase 5: 3-4 hours
- Phase 6: 2-3 hours
- Phase 7: 3-4 hours

**Total: ~20-27 hours**
