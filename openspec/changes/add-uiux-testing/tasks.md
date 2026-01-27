## Phase 1: Expand Playwright Test Suite

### 1.1 Core Functionality Tests
- [x] Test: Page loads with all required elements (sidebar, header, input area)
- [x] Test: Entry meta label shows agent and model info
- [x] Test: Header tabs are visible (Chat, Data)
- [x] Test: Agent info button opens modal with correct data
- [x] Test: Settings button opens settings modal

### 1.2 Message Flow Tests
- [ ] Test: User can type and send message
- [ ] Test: Assistant message appears with streaming indicator
- [x] Test: Send button toggles to Stop during streaming
- [ ] Test: Stop button cancels streaming and reverts to Send
- [x] Test: Message meta appears under assistant message (not user)
- [ ] Test: Input is disabled during streaming

### 1.3 Provider Selection Tests
- [x] Test: Provider dropdown defaults to pipeline default
- [ ] Test: Selecting provider loads its models
- [ ] Test: Custom model input appears for OpenRouter
- [x] Test: Entry meta updates when provider/model changes
- [ ] Test: Provider selection persists across page reload

### 1.4 A/B Testing Mode Tests
- [ ] Test: A/B toggle shows warning modal on first enable
- [ ] Test: A/B mode shows two response columns
- [ ] Test: Both columns stream independently
- [ ] Test: Vote buttons appear after streaming completes
- [ ] Test: Voting collapses to winning response
- [ ] Test: Message meta is NOT shown in A/B comparison mode

### 1.5 Conversation Management Tests
- [x] Test: New chat button clears messages
- [ ] Test: Conversation appears in sidebar after first message
- [ ] Test: Clicking conversation in sidebar loads its messages
- [ ] Test: Delete button removes conversation

### 1.6 Agent Info Modal Tests
- [x] Test: Modal opens on button click (covered by "opens modal with correct data")
- [x] Test: Modal shows agent name, model, pipeline, embedding, sources
- [x] Test: Modal closes on backdrop click
- [x] Test: Modal closes on X button click (covered by "opens modal with correct data")
- [x] Test: Modal closes on Escape key

### 1.7 Data Tab Tests
- [ ] Test: Data tab click with conversation navigates to /data
- [x] Test: Data tab click without conversation shows alert message

### 1.8 Settings Modal Tests
- [x] Test: Settings modal opens with Models section active
- [x] Test: Can switch between Models, API Keys, Advanced sections
- [ ] Test: Trace verbose mode persists
- [x] Test: Modal closes on backdrop click

## Phase 2: MCP Manual Validation Checklists

### 2.1 Visual Quality Checks (run via Chrome MCP)
- [x] Check: Header tabs have correct active state styling
- [x] Check: Entry meta label is legible and properly positioned
- [x] Check: Message meta is styled consistently with design system
- [x] Check: Agent info modal has proper spacing and typography
- [ ] Check: All buttons have visible hover/focus states
- [ ] Check: Color contrast meets accessibility standards

### 2.2 Interaction Quality Checks
- [ ] Check: Tab order is logical (input → config → settings → agent info → send)
- [ ] Check: Focus is visible on all interactive elements
- [ ] Check: Modals trap focus appropriately
- [x] Check: Escape closes all modals
- [x] Check: Click outside modal closes it

### 2.3 Layout Checks
- [ ] Check: Sidebar collapses correctly
- [ ] Check: Messages scroll to bottom on new message
- [ ] Check: Long messages wrap correctly
- [ ] Check: Code blocks don't overflow

### 2.4 Console Health Checks
- [x] Check: No JavaScript errors in console
- [x] Check: No 4xx/5xx network errors
- [ ] Check: No CORS warnings

## Phase 3: Bug Fixes

### 3.1 Known Bug Fixes
- [x] Fix: Data tab shows alert instead of crash when no conversation (was already working)
- [x] Fix: Entry meta shows selected config name, not "Default agent"
- [ ] Fix: A/B comparison messages don't show message meta
- [x] Fix: Header active tab has clear visual distinction

### 3.2 Styling Improvements
- [x] Improve: Agent info modal visual polish
- [x] Improve: Entry meta positioning and readability
- [x] Improve: Message meta subtle styling

## Phase 4: Documentation

### 4.1 Test Documentation
- [x] Document: How to run Playwright tests (tests/ui/README.md)
- [x] Document: How to run MCP manual checks (tests/ui/manual-checks.md)
- [x] Document: Test patterns for new features (tests/ui/README.md)
