# Change: Connect Chat UI to Backend APIs

## Why
The chat UI has been redesigned with streaming support, agent traces, A/B testing, and conversation history features. The backend APIs already exist for all these capabilities, but the frontend-to-backend integration needs verification and completion to ensure a fully functional user experience.

## What Changes
- **Streaming API Integration**: Ensure frontend correctly handles SSE streaming events from `/api/get_chat_response_stream`
- **Agent Trace Display**: Connect trace UI components to `/api/trace` endpoints
- **A/B Testing Backend**: Wire up A/B preference voting to `/api/ab/*` endpoints
- **Conversation Persistence**: Verify conversation CRUD operations work end-to-end

## Impact
- Affected specs: chat-api (new)
- Affected code: 
  - `src/interfaces/chat_app/static/chat.js` - API integration
  - `src/interfaces/chat_app/app.py` - Backend handlers (verification)
  - `src/utils/sql.py` - Database queries (verification)

## Current State Analysis

### Backend APIs (Implemented)
| Endpoint | Method | Status | Purpose |
|----------|--------|--------|---------|
| `/api/get_chat_response_stream` | POST | ✅ Exists | SSE streaming responses with tool calls |
| `/api/get_configs` | GET | ✅ Exists | List available model configurations |
| `/api/list_conversations` | POST | ✅ Exists | Get conversation history |
| `/api/load_conversation` | POST | ✅ Exists | Load specific conversation |
| `/api/new_conversation` | POST | ✅ Exists | Create new conversation |
| `/api/delete_conversation` | POST | ✅ Exists | Delete conversation |
| `/api/ab/create` | POST | ✅ Exists | Create A/B comparison |
| `/api/ab/preference` | POST | ✅ Exists | Record A/B preference vote |
| `/api/ab/pending` | POST | ✅ Exists | Get pending A/B comparison |
| `/api/trace` | GET | ✅ Exists | Get agent trace by ID |
| `/api/cancel_stream` | POST | ✅ Exists | Cancel streaming request |

### Frontend API Usage (Needs Verification)
- [ ] Streaming event parsing matches backend format
- [ ] Agent trace display uses correct event structure
- [ ] A/B testing UI triggers correct API calls
- [ ] Conversation sidebar syncs with backend
- [ ] Error handling covers all API failure modes

## Success Criteria
1. User can send a message and see streamed response
2. Agent tool calls display in real-time during streaming
3. A/B comparison mode generates two responses and allows voting
4. Conversation history persists across page reloads
5. Cancel button stops active streaming requests
