# Frontend UI Improvements with Streaming and BYOK Providers

## Summary

This PR delivers a comprehensive overhaul of the A2rchi chat interface with modern UX patterns, real-time token streaming, and a flexible provider system that allows users to bring their own API keys (BYOK).

## Screenshots

### Landing Page
![Landing Page](https://raw.githubusercontent.com/mit-submit/A2rchi/frontend-ui-improvements/docs/docs/_static/screenshots/landing-page.png)
*Modern welcome screen with quick access to features*

### Chat Interface
![Chat Interface](https://raw.githubusercontent.com/mit-submit/A2rchi/frontend-ui-improvements/docs/docs/_static/screenshots/chat-interface.png)
*ChatGPT-style interface with sidebar conversation history*

### Chat with Streaming Response
![Chat Response](https://raw.githubusercontent.com/mit-submit/A2rchi/frontend-ui-improvements/docs/docs/_static/screenshots/chat-response.png)
*Markdown rendering with syntax highlighting and agent metadata*

### Settings Panel - Model Selection
![Settings Panel](https://raw.githubusercontent.com/mit-submit/A2rchi/frontend-ui-improvements/docs/docs/_static/screenshots/settings-panel.png)
*Provider and model selection with dynamic Ollama model discovery*

### Settings Panel - API Keys (BYOK)
![API Keys](https://raw.githubusercontent.com/mit-submit/A2rchi/frontend-ui-improvements/docs/docs/_static/screenshots/api-keys-panel.png)
*Secure API key management for multiple providers*

### Data Viewer
![Data Viewer](https://raw.githubusercontent.com/mit-submit/A2rchi/frontend-ui-improvements/docs/docs/_static/screenshots/data-viewer.png)
*Document management interface for viewing and filtering ingested data*

## Key Features

### 1. Chat UI Overhaul
- **Modern ChatGPT-style interface** with collapsible sidebar
- **Conversation history** with search and delete functionality
- **Redesigned input bar** as single pill-shaped container
- **Client-side markdown rendering** with marked.js + highlight.js
- **Code block syntax highlighting** with copy button
- **Mobile-responsive design** with accessibility improvements

### 2. Real-Time Token Streaming
- **Multi-mode streaming** (`messages` + `updates`) for token-level output
- **Cancel stream button** during active responses
- **Progressive text display** with cursor animation
- **Agent activity indicator** showing tool calls and reasoning

### 3. BYOK (Bring Your Own Key) Provider System
- **Multiple provider support**: OpenAI, Anthropic, OpenRouter, Google Gemini, Local (Ollama/vLLM)
- **Dynamic model discovery** from Ollama API with size display (e.g., "qwen3:4b (4.0B)")
- **Secure key storage** in browser session (never logged or sent to server)
- **Environment variable fallback** for server-configured keys

### 4. Data Viewer
- **Document catalog** showing all ingested sources
- **Filter by type**: Local Files, Web Pages, Tickets
- **Enable/disable documents** for selective retrieval
- **Document preview** with metadata

### 5. Playwright UI Tests
- Comprehensive test coverage for chat workflows
- Streaming behavior tests
- Provider switching tests
- Conversation management tests

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   chat.js   │  │   chat.css  │  │   index.html        │  │
│  │ (streaming, │  │ (modern UI) │  │ (settings modal,    │  │
│  │  markdown)  │  │             │  │  provider panels)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Backend                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   app.py    │  │ api_v2.py   │  │  base_react.py      │  │
│  │ (endpoints) │  │ (data API)  │  │ (multi-mode stream) │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Provider System                         │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────┐  │    │
│  │  │ OpenAI  │ │Anthropic│ │OpenRouter│ │Local/Ollama│  │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └───────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Files Changed

| Category | Files | Description |
|----------|-------|-------------|
| UI | `chat.js`, `index.html` | Modern streaming interface |
| Backend | `app.py`, `api_v2.py` | API endpoints and streaming |
| Streaming | `base_react.py` | Multi-mode token streaming |
| Providers | `src/a2rchi/providers/*` | BYOK provider implementations |
| Data Viewer | `data_viewer_service.py`, `v2-api.js` | Document management |
| Tests | `tests/ui/*.spec.ts` | Playwright UI tests |
| Docs | `user_guide.md`, `api_reference.md` | Updated documentation |
| Specs | `openspec/changes/*` | Design proposals |

## Configuration

### Provider Selection (UI Settings)
Users can select providers and enter API keys directly in the UI:
- **Local Server** (Ollama/vLLM) - No key required
- **OpenAI** - Requires `OPENAI_API_KEY` or user-provided key
- **Anthropic** - Requires `ANTHROPIC_API_KEY` or user-provided key
- **OpenRouter** - Requires `OPENROUTER_API_KEY` or user-provided key
- **Google Gemini** - Requires `GOOGLE_API_KEY` or user-provided key

### Dynamic Ollama Models
When using Local Server provider with Ollama, models are automatically discovered:
```
GET http://{OLLAMA_HOST}/api/tags
```
Response shows model name and size: `qwen3:4b (4.0B)`, `qwen2.5-coder:3b (3.1B)`

## Verification Plan

### Automated Tests
```bash
# Run Playwright UI tests
cd tests/ui && npx playwright test

# Specific test suites
npx playwright test chat.spec.ts
npx playwright test workflows/04-streaming.spec.ts
npx playwright test workflows/05-providers.spec.ts
```

### Manual Verification

1. **Chat Interface**
   - [ ] Open http://localhost:7861
   - [ ] Click "Get Started" to enter chat
   - [ ] Verify sidebar shows conversation history
   - [ ] Send a message, verify streaming response with token-by-token display
   - [ ] Verify markdown rendering and code highlighting

2. **Settings Panel**
   - [ ] Click Settings gear icon
   - [ ] Verify provider dropdown shows all options
   - [ ] Select "Local Server", verify Ollama models populate dynamically
   - [ ] Check API Keys tab shows status indicators (✓ for configured, ○ for missing)

3. **BYOK Providers**
   - [ ] Enter an OpenAI API key in Settings > API Keys
   - [ ] Switch provider to OpenAI
   - [ ] Send a message, verify response comes from OpenAI

4. **Data Viewer**
   - [ ] Click "Data" tab in navigation
   - [ ] Verify document list loads
   - [ ] Test filters (type, enabled state)
   - [ ] Click a document to preview

5. **Mobile Responsiveness**
   - [ ] Open on mobile viewport (375px width)
   - [ ] Verify sidebar collapses to hamburger menu
   - [ ] Test touch interactions

## OpenSpec Proposals

This PR implements the following design proposals:
- `openspec/changes/add-byok-api-keys/` - BYOK provider system
- `openspec/changes/add-data-viewer/` - Document management UI
- `openspec/changes/add-uiux-testing/` - Playwright test infrastructure
- `openspec/changes/multi-provider-models/` - Provider abstraction
- `openspec/changes/connect-chat-backend/` - Chat API improvements

## Breaking Changes

None. This PR is additive and backward-compatible.

## Dependencies

Frontend (loaded via CDN):
- `marked.js` - Markdown parsing
- `highlight.js` - Syntax highlighting

Backend (already in requirements):
- `langchain_ollama` - Ollama integration
- `langchain_openai` - OpenAI integration
- `langchain_anthropic` - Anthropic integration

## Related Issues

- Implements modern chat UI (#XXX)
- Adds BYOK provider support (#XXX)
- Improves streaming experience (#XXX)
