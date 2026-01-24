## 1. Test Infrastructure Setup
- [ ] 1.1 Navigate to chat application at localhost:2000
- [ ] 1.2 Verify page loads successfully with all UI elements

## 2. Message Input Tests
- [ ] 2.1 Verify input field is visible and focusable
- [ ] 2.2 Type text and verify it appears in input
- [ ] 2.3 Send message via Enter key
- [ ] 2.4 Send message via click send button
- [ ] 2.5 Verify empty message cannot be sent
- [ ] 2.6 Verify input is disabled during streaming
- [ ] 2.7 Verify input is re-enabled after streaming completes

## 3. Response Streaming Tests
- [ ] 3.1 Verify assistant message bubble appears on send
- [ ] 3.2 Verify streaming cursor appears during response
- [ ] 3.3 Verify text streams incrementally
- [ ] 3.4 Verify markdown renders correctly (bold, lists, code)
- [ ] 3.5 Verify streaming cursor disappears on completion
- [ ] 3.6 Verify code blocks are syntax highlighted after completion

## 4. Agent Trace Tests - Normal Mode
- [ ] 4.1 Send message that triggers tool usage
- [ ] 4.2 Verify "Agent Activity" container appears
- [ ] 4.3 Verify tool blocks show tool name and "Running..." status
- [ ] 4.4 Verify tool blocks update with output on completion
- [ ] 4.5 Verify tool blocks show duration
- [ ] 4.6 Verify trace header shows tool count after completion
- [ ] 4.7 Verify trace auto-collapses in normal mode
- [ ] 4.8 Verify trace can be expanded/collapsed by clicking header

## 5. Agent Trace Tests - Verbose Mode
- [ ] 5.1 Open settings and select "Verbose" mode
- [ ] 5.2 Send message that triggers tool usage
- [ ] 5.3 Verify tool arguments are visible/expanded
- [ ] 5.4 Verify tool output is visible/expanded
- [ ] 5.5 Verify trace does NOT auto-collapse

## 6. Agent Trace Tests - Minimal Mode
- [ ] 6.1 Open settings and select "Minimal" mode
- [ ] 6.2 Send message that triggers tool usage
- [ ] 6.3 Verify NO trace container appears
- [ ] 6.4 Verify response still displays correctly

## 7. A/B Testing Mode - Setup
- [ ] 7.1 Open settings modal
- [ ] 7.2 Enable A/B testing toggle
- [ ] 7.3 Verify second config dropdown appears
- [ ] 7.4 Select different configs for A and B
- [ ] 7.5 Close settings modal

## 8. A/B Testing Mode - Response Display
- [ ] 8.1 Send message in A/B mode
- [ ] 8.2 Verify two response columns appear side-by-side
- [ ] 8.3 Verify columns labeled "Model A" and "Model B"
- [ ] 8.4 Verify both columns stream responses
- [ ] 8.5 Verify each column has its own trace container (if not minimal mode)

## 9. A/B Testing Mode - Voting
- [ ] 9.1 Wait for both responses to complete
- [ ] 9.2 Verify vote buttons appear (Model A / Model B)
- [ ] 9.3 Click vote for Model A
- [ ] 9.4 Verify comparison collapses to single winning response
- [ ] 9.5 Verify winning response's trace is preserved
- [ ] 9.6 Verify input is re-enabled after voting

## 10. A/B Testing Mode - Vote for B
- [ ] 10.1 Send another message in A/B mode
- [ ] 10.2 Vote for Model B
- [ ] 10.3 Verify Model B's response and trace are preserved

## 11. Conversation Management - Create
- [ ] 11.1 Click "+" button in sidebar
- [ ] 11.2 Verify chat area clears
- [ ] 11.3 Verify new conversation appears in sidebar
- [ ] 11.4 Send a message to populate new conversation

## 12. Conversation Management - Switch
- [ ] 12.1 Click on a different conversation in sidebar
- [ ] 12.2 Verify chat area loads that conversation's messages
- [ ] 12.3 Verify correct conversation is highlighted in sidebar
- [ ] 12.4 Click back to original conversation
- [ ] 12.5 Verify original messages are restored

## 13. Conversation Management - Delete
- [ ] 13.1 Hover over a conversation in sidebar
- [ ] 13.2 Click delete button
- [ ] 13.3 Verify confirmation dialog appears
- [ ] 13.4 Confirm deletion
- [ ] 13.5 Verify conversation is removed from sidebar

## 14. Settings Modal Tests
- [ ] 14.1 Click settings icon (gear)
- [ ] 14.2 Verify modal opens
- [ ] 14.3 Verify all settings sections are visible
- [ ] 14.4 Click outside modal to close
- [ ] 14.5 Verify modal closes
- [ ] 14.6 Re-open and close via close button (X)

## 15. Settings Persistence Tests
- [ ] 15.1 Change verbose mode setting
- [ ] 15.2 Close and re-open settings
- [ ] 15.3 Verify setting persisted
- [ ] 15.4 Refresh page
- [ ] 15.5 Open settings and verify setting still persisted

## 16. Response Cancellation Tests
- [ ] 16.1 Send a message
- [ ] 16.2 Verify "Stop" button appears during streaming
- [ ] 16.3 Click Stop button
- [ ] 16.4 Verify streaming stops
- [ ] 16.5 Verify partial response preserved with "cancelled" notice
- [ ] 16.6 Verify input is re-enabled

## 17. Error Handling Tests
- [ ] 17.1 Test behavior when agent returns error
- [ ] 17.2 Verify error message displays in red/error style
- [ ] 17.3 Verify input is re-enabled after error

## 18. Edge Cases
- [ ] 18.1 Rapid message sending (click send multiple times quickly)
- [ ] 18.2 Very long message input
- [ ] 18.3 Special characters in message (HTML, markdown, emoji)
- [ ] 18.4 Message with only whitespace
- [ ] 18.5 Switch conversation during streaming (should be blocked or handled)

## 19. Visual/UI Consistency
- [ ] 19.1 Verify message alignment (user right, assistant left)
- [ ] 19.2 Verify avatar icons display correctly
- [ ] 19.3 Verify timestamps/sender labels are correct
- [ ] 19.4 Verify scrolling behavior (auto-scroll to bottom on new message)
- [ ] 19.5 Verify hover states on buttons

## 20. Responsive Layout (if time permits)
- [ ] 20.1 Resize viewport to mobile width (<768px)
- [ ] 20.2 Verify sidebar collapses/hamburger menu appears
- [ ] 20.3 Verify A/B comparison stacks vertically on mobile

## 21. Accessibility Validation
- [ ] 21.1 Check page has proper heading hierarchy (h1 > h2 > h3)
- [ ] 21.2 Verify all interactive elements are keyboard accessible
- [ ] 21.3 Tab through page - verify logical focus order
- [ ] 21.4 Verify focus indicators are visible on interactive elements
- [ ] 21.5 Check all buttons have accessible names
- [ ] 21.6 Check all form inputs have labels
- [ ] 21.7 Verify color contrast meets WCAG AA (4.5:1 for text)
- [ ] 21.8 Check ARIA roles are used correctly
- [ ] 21.9 Verify screen reader can navigate message history
- [ ] 21.10 Verify live regions announce new messages

## 22. Console & Network Health
- [ ] 22.1 Check for JavaScript errors in console
- [ ] 22.2 Check for console warnings
- [ ] 22.3 Verify no failed network requests (4xx/5xx)
- [ ] 22.4 Check for CORS errors
- [ ] 22.5 Verify WebSocket/SSE connections succeed

## 23. Performance Validation
- [ ] 23.1 Run performance trace on page load
- [ ] 23.2 Check Largest Contentful Paint (LCP) < 2.5s
- [ ] 23.3 Check First Input Delay (FID) / Interaction to Next Paint (INP)
- [ ] 23.4 Check Cumulative Layout Shift (CLS) < 0.1
- [ ] 23.5 Verify no layout shifts during message streaming
- [ ] 23.6 Check memory usage doesn't grow unbounded with messages

## 24. Semantic HTML & Structure
- [ ] 24.1 Verify page has single h1 (page title)
- [ ] 24.2 Check main content is in <main> landmark
- [ ] 24.3 Check sidebar navigation uses <nav> landmark
- [ ] 24.4 Verify buttons use <button> not <div> with onclick
- [ ] 24.5 Check form elements have proper types
- [ ] 24.6 Verify lists use <ul>/<ol>/<li> appropriately
- [ ] 24.7 Check images have alt text (if any)

## 25. Design Consistency
- [ ] 25.1 Verify consistent spacing (8px grid system)
- [ ] 25.2 Check typography scale consistency
- [ ] 25.3 Verify color palette is consistent (CSS variables used)
- [ ] 25.4 Check border radius consistency
- [ ] 25.5 Verify shadow/elevation consistency
- [ ] 25.6 Check icon sizing consistency
- [ ] 25.7 Verify loading states exist for all async operations

## 26. Empty & Error States
- [ ] 26.1 Verify empty conversation state has helpful message
- [ ] 26.2 Check empty sidebar state (no conversations)
- [ ] 26.3 Verify error states are visually distinct
- [ ] 26.4 Check error messages are user-friendly (not technical)
- [ ] 26.5 Verify recovery paths exist from error states

## 27. Interaction Design Quality
- [ ] 27.1 Verify click targets are >= 44x44px (touch friendly)
- [ ] 27.2 Check hover states provide clear affordance
- [ ] 27.3 Verify disabled states are visually distinct
- [ ] 27.4 Check active/pressed states exist
- [ ] 27.5 Verify transitions are smooth (not jarring)
- [ ] 27.6 Check animations respect prefers-reduced-motion

## 28. Code Quality Checks
- [ ] 28.1 Run ESLint on chat.js (if configured)
- [ ] 28.2 Check CSS for unused selectors
- [ ] 28.3 Verify no inline styles (should use CSS classes)
- [ ] 28.4 Check for console.log statements (should be removed)
- [ ] 28.5 Verify event listeners are properly cleaned up
- [ ] 28.6 Check for memory leaks in long-running sessions
