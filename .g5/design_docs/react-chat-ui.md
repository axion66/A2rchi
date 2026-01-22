# ChatScope React Chat UI Design Document

## Overview

Modernize the A2rchi chat experience by replacing the current vanilla JS + custom CSS interface with the ChatScope React chat UI kit. The new interface should feel comparable to ChatGPT in layout, spacing, and clarity while preserving the existing Flask backend APIs, streaming protocol, and data flows.

## Goals

1. Adopt ChatScope as the primary UI component library for the chat interface.
2. Preserve streaming behavior with incremental rendering of markdown and syntax-highlighted code blocks.
3. Maintain existing backend endpoints and payloads (no API changes).
4. Retain current functional parity: conversation list, config selector, and feedback controls.
5. Add A/B testing support that can display two model responses for the same user prompt with clear labeling.

## Non-Goals

- Rewriting backend Flask APIs or database schema.
- Changing streaming protocol (NDJSON event types remain unchanged).
- Introducing server-side rendering (client-rendered only).
- Rewriting backend endpoints or database schemas.
- Building a full React application shell beyond the chat interface.

## Success Criteria

- [ ] Chat UI renders using ChatScope with a ChatGPT-like layout, spacing, and typography.
- [ ] Streaming responses render incrementally with markdown + code blocks and remain readable mid-stream.
- [ ] Existing endpoints (/api/get_chat_response_stream, /conversations, /feedback, /configs) work unchanged.
- [ ] Conversation list (sessions) is visible in the left sidebar and is functional.
- [ ] Model selector is available in the UI and maps to existing configs.
- [ ] A/B testing view shows two responses (Model A / Model B) for the same prompt.
- [ ] Code block formatting remains consistent with the current UI.

---

## Affected Specs

| Spec | Action | Reason |
|------|--------|--------|
| `.g5/specs/interfaces/chat-app.spec.md` | Update | UI implementation changes and frontend stack details |

## Implementation Notes

- **UI framework**: Use ChatScope (`@chatscope/chat-ui-kit-react`) for the layout and message components.
- **Bundling**: Add a small React build step that outputs bundled assets into `src/interfaces/chat_app/static/` for Flask to serve.
- **Markdown rendering**: Maintain client-side markdown rendering with code highlighting (keep `marked.js` + `highlight.js` unless a React markdown renderer proves more compatible).
- **Streaming**: Preserve the NDJSON streaming contract and render partial content incrementally; finalize on `final` event with a complete render.
- **A/B responses**: Render two assistant responses per user prompt, labeled by model name and grouped together (default: stacked; revisit if side-by-side is preferred).
- **Styling**: Use ChatGPT-like typography, spacing, and neutral color palette; ensure code blocks remain legible.
- **Compatibility**: Preserve existing non-streaming fallback and feedback actions.

## Open Questions

1. Do we prefer Vite or a minimal bundler for the React build pipeline?
2. Should we keep `marked.js` or move to a React markdown renderer (e.g., `react-markdown`)?
3. Should A/B responses render side-by-side or stacked (default: stacked)?
