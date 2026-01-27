## 1. Verify Streaming Integration

- [ ] 1.1 Test message submission triggers streaming request
- [ ] 1.2 Verify SSE event parsing handles all event types (chunk, tool_start, tool_output, tool_end, error, done)
- [ ] 1.3 Test streaming text renders correctly with markdown
- [ ] 1.4 Verify conversation_id is tracked across messages
- [ ] 1.5 Test error handling for network failures

## 2. Agent Trace Integration

- [ ] 2.1 Verify tool_start events display tool name and args
- [ ] 2.2 Verify tool_output events display truncated output with expand option
- [ ] 2.3 Verify tool_end events show status and duration
- [ ] 2.4 Test trace toggle button shows/hides trace details
- [ ] 2.5 Verify trace persists after streaming completes (fetch from /api/trace if needed)

## 3. A/B Testing Integration

- [ ] 3.1 Test enabling A/B mode via settings toggle
- [ ] 3.2 Verify A/B warning modal displays on first enable
- [ ] 3.3 Test dual model selection in A/B mode
- [ ] 3.4 Verify two parallel streaming requests in A/B mode
- [ ] 3.5 Test vote buttons call /api/ab/preference
- [ ] 3.6 Verify voted response is marked as winner
- [ ] 3.7 Test "It's a tie" option

## 4. Conversation Persistence

- [ ] 4.1 Verify new conversations appear in sidebar
- [ ] 4.2 Test loading existing conversation restores messages
- [ ] 4.3 Verify conversation title updates after first message
- [ ] 4.4 Test delete conversation removes from sidebar and backend
- [ ] 4.5 Verify client_id is persisted in localStorage

## 5. Cancel Stream Integration

- [ ] 5.1 Test cancel button appears during streaming
- [ ] 5.2 Verify cancel request stops server-side processing
- [ ] 5.3 Test cancelled message shows appropriate indicator
- [ ] 5.4 Verify user can send new message after cancel

## 6. Error Handling

- [ ] 6.1 Test 401 response redirects to login (if auth enabled)
- [ ] 6.2 Test 500 response shows error message
- [ ] 6.3 Test network timeout shows retry option
- [ ] 6.4 Verify partial responses are preserved on error
