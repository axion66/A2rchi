## Context

The chat application (`src/interfaces/chat_app/`) has grown to include:
- Real-time streaming responses with markdown rendering
- Agent trace display (tool calls, outputs, durations)
- A/B testing comparison mode with voting
- Conversation management (create, switch, delete)
- Settings modal with persistence
- Response cancellation

Manual testing is error-prone and time-consuming. We need automated end-to-end tests.

## Goals / Non-Goals

**Goals:**
- Automate all functional UI tests
- Cover every user-facing feature
- Catch regressions before deployment
- Minimize manual testing to edge cases only

**Non-Goals:**
- Visual regression testing (pixel-perfect comparisons)
- Performance/load testing
- Backend unit testing (separate concern)
- Cross-browser testing (Chrome only for now)

## Testing Approach

### Tool: Chrome DevTools MCP

We'll use the Chrome DevTools MCP tools which provide:
- `navigate_page` - Load the application
- `take_snapshot` - Get accessibility tree (element UIDs)
- `click` - Interact with elements
- `fill` - Type into input fields
- `wait_for` - Wait for text to appear
- `evaluate_script` - Run JavaScript for complex assertions
- `take_screenshot` - Capture state for debugging

### Test Flow Pattern

Each test follows this pattern:
1. **Arrange**: Navigate to page, set up state
2. **Act**: Perform user actions (click, type, etc.)
3. **Assert**: Verify expected outcome (wait_for text, check snapshot)

### Element Selection Strategy

Use the accessibility tree snapshot to find elements by:
- Role (button, textbox, heading)
- Name/label
- Unique identifiers in the DOM

### Handling Async Operations

For streaming responses:
1. Send message
2. Use `wait_for` to wait for completion indicators
3. Take snapshot to verify final state

### State Management Between Tests

- Use `evaluate_script` to clear localStorage between test groups
- Create new conversations to isolate tests
- Refresh page between major test sections

## Test Categories

### 1. Smoke Tests (Critical Path)
- Page loads
- Can send message
- Response appears
- Input re-enables

### 2. Feature Tests
- Agent traces (all verbose modes)
- A/B testing (enable, vote, winner)
- Conversations (CRUD)
- Settings (open, change, persist)
- Cancellation

### 3. Edge Case Tests
- Empty input
- Rapid interactions
- Error states

### 4. Quality Validation Tests

#### Accessibility (via Chrome MCP)
| Check | Method |
|-------|--------|
| Heading hierarchy | `take_snapshot` - parse heading levels |
| Keyboard navigation | `press_key('Tab')` repeatedly, verify focus moves |
| Focus indicators | `take_screenshot` after focus, visual check |
| Button accessibility | `take_snapshot` - verify button names |
| ARIA roles | `evaluate_script` - query ARIA attributes |
| Color contrast | `evaluate_script` - compute contrast ratios |

#### Console & Network Health
| Check | Method |
|-------|--------|
| JS errors | `list_console_messages(types=['error'])` |
| Warnings | `list_console_messages(types=['warn'])` |
| Failed requests | `list_network_requests()` - filter 4xx/5xx |
| CORS errors | `list_console_messages` - filter CORS |

#### Performance
| Check | Method |
|-------|--------|
| Core Web Vitals | `performance_start_trace(reload=true)` → `performance_stop_trace()` |
| LCP, FID, CLS | Parse trace results |
| Memory leaks | `evaluate_script` - check `performance.memory` over time |
| Layout shifts | `performance_analyze_insight('LayoutShifts')` |

#### Semantic HTML
| Check | Method |
|-------|--------|
| Single h1 | `evaluate_script` - `document.querySelectorAll('h1').length === 1` |
| Landmarks | `evaluate_script` - check main, nav, header elements |
| Button elements | `evaluate_script` - verify no div[onclick] without role=button |
| Label association | `evaluate_script` - check inputs have labels |

#### Design Consistency
| Check | Method |
|-------|--------|
| CSS variables used | `evaluate_script` - count inline styles vs classes |
| Spacing grid | `evaluate_script` - sample margins/paddings, verify 4/8px multiples |
| Consistent borders | `evaluate_script` - sample border-radius values |
| Touch targets | `evaluate_script` - measure clickable element dimensions |

## Automated vs Manual Checks

### Fully Automatable (Chrome MCP)
- Console errors/warnings
- Network failures
- Heading structure
- Button accessibility names
- ARIA attributes
- Element dimensions
- CSS variable usage
- Performance traces
- Keyboard navigation flow

### Semi-Automated (Chrome MCP + Human Review)
- Color contrast (can compute, but edge cases need judgment)
- Focus indicators (can screenshot, human verifies visibility)
- Touch targets (can measure, human judges adequacy)
- Animation smoothness (can trace, human judges feel)

### Manual Review Required
- Overall visual aesthetics
- Copywriting quality
- User flow intuitiveness
- Brand consistency
- Edge case UX decisions

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Flaky tests due to timing | Use `wait_for` liberally, add reasonable timeouts |
| Element selection fragility | Use semantic selectors (role, label) over CSS classes |
| Test isolation | Clear state between test groups |
| Long test runtime | Parallelize where possible, group related tests |

## Open Questions

- Should we record screenshots for each test step for debugging?
- How to handle tests that require specific agent behavior (tool calls)?
- Should we mock the backend for faster/deterministic tests?
