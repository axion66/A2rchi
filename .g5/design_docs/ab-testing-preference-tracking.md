# Design Document: A/B Testing with Preference Tracking

## Summary

Add backend support for A/B testing in the A2rchi chat UI, allowing users to compare two model responses side-by-side (like ChatGPT/Gemini) and vote for their preferred response. User preferences are recorded in PostgreSQL for analysis.

---

## User Intent

The user wants to:
1. Enable A/B testing mode via the existing (non-functional) toggle in settings
2. See two responses for the same prompt, labeled "Model A" and "Model B" 
3. Click on the response they prefer (similar to ChatGPT/Gemini's "regenerate and compare" UX)
4. Have their preference recorded in PostgreSQL for later analysis (e.g., ELO ratings, preference analytics)

---

## Current State

### Existing A/B Toggle (Frontend)
- Settings toggle exists at [index.html#L103-L108](src/interfaces/chat_app/templates/index.html#L103-L108)
- JavaScript handles toggle state in `UI.isABEnabled()` at [chat.js#L442](src/interfaces/chat_app/static/chat.js#L442)
- When A/B enabled, two responses stream in parallel at [chat.js#L786-L798](src/interfaces/chat_app/static/chat.js#L786-L798)
- Responses show labels like "Model A: config_name" and "Model B: config_name"

### Current Limitations
1. **No preference collection** - Users cannot vote on which response is better
2. **No backend tracking** - A/B pairs are not linked in the database
3. **No feedback UI** - No visual indication that users should/can choose a preferred response
4. **Responses stored independently** - Each response is just a regular message with no A/B context

### Existing Database Schema
- `conversations` table stores messages with `message_id`, `sender`, `content`, `conf_id`
- `feedback` table stores like/dislike/comments per message
- `configs` table tracks which config (model) was used

---

## Proposed Design

### UX Flow (Gemini/ChatGPT Style)

```
┌─────────────────────────────────────────────────────────────────────┐
│ User: "What is quantum computing?"                                  │
├─────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────┐ ┌─────────────────────────────────┐ │
│ │ Response A                  │ │ Response B                      │ │
│ │ (gpt-4o-mini)               │ │ (claude-3-haiku)                │ │
│ ├─────────────────────────────┤ ├─────────────────────────────────┤ │
│ │ Quantum computing uses      │ │ Quantum computing harnesses     │ │
│ │ qubits instead of bits...   │ │ quantum mechanics to process... │ │
│ │                             │ │                                 │ │
│ │ [More content...]           │ │ [More content...]               │ │
│ ├─────────────────────────────┤ ├─────────────────────────────────┤ │
│ │  [ 👍 Better ]              │ │  [ 👍 Better ]                  │ │
│ └─────────────────────────────┘ └─────────────────────────────────┘ │
│                         [ 🤝 Tie ]                                   │
└─────────────────────────────────────────────────────────────────────┘
```

**After voting:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────────────────┐ ┌─────────────────────────────────┐ │
│ │ Response A ✓ (Chosen)       │ │ Response B                      │ │
│ │ (gpt-4o-mini)               │ │ (claude-3-haiku)                │ │
│ ├─────────────────────────────┤ ├─────────────────────────────────┤ │
│ │ ...                         │ │ ...                             │ │
│ ├─────────────────────────────┤ ├─────────────────────────────────┤ │
│ │  ✓ You chose this           │ │  (faded/de-emphasized)          │ │
│ └─────────────────────────────┘ └─────────────────────────────────┘ │
│                   [ Thank you for your feedback! ]                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Design Decisions

**Q1: Side-by-side vs. stacked layout?**
- **Decision: Side-by-side** on desktop (>768px), stacked on mobile
- Rationale: Side-by-side makes comparison easier; stacked is current default for mobile

**Q2: Should users be able to skip voting?**
- **Decision: No - Forced voting** - Users must vote before sending another message
- This ensures we collect preference data for every A/B comparison
- After voting, both responses collapse to just the winning response (or response A if tie)

**Q3: What choices should users have?**
- **Decision: Three options** - "A is better", "B is better", "Tie / Both are good"
- This matches industry standard (ChatGPT, Gemini, Claude)

**Q4: Should we track which config is A vs B or anonymize?**
- **Decision: Fully anonymous display** - Store config_id for both A and B internally
- Display "Model A" / "Model B" to user always (never reveal config names)
- Randomize which config gets assigned to A vs B per comparison
- Prevents bias toward familiar/preferred model names and position bias

**Q5: What about continuing the conversation after A/B?**
- **Decision: Use the winning response** as the canonical history entry
- If tie or skipped, use Response A as canonical
- Store both responses in database for analysis

---

## Database Schema Changes

### New Table: `ab_comparisons`

```sql
CREATE TABLE IF NOT EXISTS ab_comparisons (
    comparison_id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    user_prompt_mid INTEGER NOT NULL,         -- message_id of the user's question
    response_a_mid INTEGER NOT NULL,          -- message_id of response A
    response_b_mid INTEGER NOT NULL,          -- message_id of response B
    config_a_id INTEGER NOT NULL,             -- config used for response A
    config_b_id INTEGER NOT NULL,             -- config used for response B
    preference TEXT,                          -- 'a', 'b', 'tie', or NULL (not yet voted)
    preference_ts TIMESTAMP,                  -- when the preference was recorded
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    FOREIGN KEY (conversation_id) REFERENCES conversation_metadata(conversation_id) ON DELETE CASCADE,
    FOREIGN KEY (user_prompt_mid) REFERENCES conversations(message_id) ON DELETE CASCADE,
    FOREIGN KEY (response_a_mid) REFERENCES conversations(message_id) ON DELETE CASCADE,
    FOREIGN KEY (response_b_mid) REFERENCES conversations(message_id) ON DELETE CASCADE,
    FOREIGN KEY (config_a_id) REFERENCES configs(config_id),
    FOREIGN KEY (config_b_id) REFERENCES configs(config_id)
);

-- Index for efficient queries
CREATE INDEX idx_ab_comparisons_conversation ON ab_comparisons(conversation_id);
CREATE INDEX idx_ab_comparisons_configs ON ab_comparisons(config_a_id, config_b_id);
CREATE INDEX idx_ab_comparisons_preference ON ab_comparisons(preference) WHERE preference IS NOT NULL;
```

### SQL Queries to Add

```python
SQL_INSERT_AB_COMPARISON = """
INSERT INTO ab_comparisons (
    conversation_id, user_prompt_mid, response_a_mid, response_b_mid, 
    config_a_id, config_b_id
)
VALUES (%s, %s, %s, %s, %s, %s)
RETURNING comparison_id;
"""

SQL_UPDATE_AB_PREFERENCE = """
UPDATE ab_comparisons
SET preference = %s, preference_ts = %s
WHERE comparison_id = %s;
"""

SQL_GET_AB_COMPARISON = """
SELECT comparison_id, response_a_mid, response_b_mid, config_a_id, config_b_id, preference
FROM ab_comparisons
WHERE conversation_id = %s AND user_prompt_mid = %s;
"""
```

---

## API Changes

### New Endpoint: `POST /api/ab/preference`

Submit user preference for an A/B comparison.

**Request:**
```json
{
  "comparison_id": 123,
  "preference": "a" | "b" | "tie",
  "client_id": "abc123"
}
```

**Response:**
```json
{
  "success": true,
  "comparison_id": 123,
  "preference": "a"
}
```

### Modified: Streaming Response

When A/B mode is enabled, the final event from each stream should include metadata to link the responses:

**Current final event:**
```json
{
  "type": "final",
  "response": "...",
  "conversation_id": 123,
  "message_id": 456
}
```

**New final event (when A/B enabled):**
```json
{
  "type": "final",
  "response": "...",
  "conversation_id": 123,
  "message_id": 456,
  "ab_metadata": {
    "comparison_id": 789,
    "is_response_a": true,
    "config_name": "gpt-4o-mini"
  }
}
```

---

## Frontend Changes

### 1. Message Container Updates

Add new CSS classes for A/B comparison layout:
- `.ab-comparison-container` - Wrapper for side-by-side responses
- `.ab-response` - Individual response in comparison
- `.ab-response--winner` - Highlighted winning response
- `.ab-vote-buttons` - Vote button container
- `.ab-vote-btn` - Individual vote button

### 2. JavaScript State Updates

```javascript
// New state tracking for active A/B comparisons
const Chat = {
  state: {
    // ... existing state
    activeABComparison: null, // { comparisonId, responseAId, responseBId, voted: bool }
  },
  
  async submitABPreference(comparisonId, preference) {
    // POST to /api/ab/preference
    // Update UI to show result
    // Collapse comparison to single response for chat history
  }
};
```

### 3. A/B Response Rendering

When A/B is enabled:
1. Create side-by-side container before streaming starts
2. Stream both responses into their respective containers
3. After both complete, show vote buttons
4. On vote, update UI and send preference to backend
5. Collapse to single "canonical" response in chat flow

---

## Backend Changes

### 1. ChatWrapper Updates

Add methods to `ChatWrapper` class:
- `create_ab_comparison(conversation_id, user_mid, response_a_mid, response_b_mid, config_a_id, config_b_id)` 
- `update_ab_preference(comparison_id, preference)`

### 2. Streaming Endpoint Updates

Modify `get_chat_response_streaming()` to:
1. Accept `is_ab_mode` and `ab_role` ('a' or 'b') parameters
2. After inserting response, if this is an A/B response:
   - If response A: Create `ab_comparisons` row, return `comparison_id`
   - If response B: Update existing `ab_comparisons` row with `response_b_mid`
3. Include `ab_metadata` in final event

### 3. New Route

Add route handler in `ChatApp`:
```python
def add_endpoint('/api/ab/preference', 'ab_preference', self.submit_ab_preference, methods=['POST'])
```

---

## Migration Path

1. **Phase 1: Database** - Add `ab_comparisons` table via migration SQL
2. **Phase 2: Backend** - Add API endpoint and ChatWrapper methods
3. **Phase 3: Frontend** - Update JS to handle A/B voting UI
4. **Phase 4: Styling** - Add CSS for side-by-side layout

---

## Success Criteria

- [ ] User can enable A/B mode and see two responses side-by-side
- [ ] User can click "Better" on their preferred response
- [ ] User can click "Tie" if both are equally good
- [ ] Preference is stored in PostgreSQL `ab_comparisons` table
- [ ] After voting, UI shows clear indication of choice
- [ ] Chat continues normally using the winning response as context
- [ ] Works on mobile (stacked layout) and desktop (side-by-side)

---

## Future Considerations (Out of Scope)

1. **ELO Rating System** - Compute model rankings from preference data
2. **Blind Mode** - Option to hide model names until after voting
3. **Forced Voting** - Require vote before continuing conversation
4. **Analytics Dashboard** - Grafana views for preference analysis
5. **A/B/C Testing** - Support for more than two models

---

## Resolved Design Decisions

1. **Fully anonymous display** ✓
   - Show "Model A" / "Model B" always (never reveal config names)
   - Randomize which config gets assigned to A vs B per comparison
   - Prevents both name bias and position bias

2. **Forced voting (with opt-out)** ✓
   - Users must vote before sending another message while A/B mode is enabled
   - Input field disabled until vote is submitted
   - Users can disable A/B mode at any time if they don't want to vote
   - Show warning modal when enabling A/B mode explaining 2x API usage and voting requirement

3. **Persist comparisons on reload** ✓
   - When reloading a conversation with an incomplete A/B comparison, restore the comparison UI
   - User must vote before continuing (or disable A/B mode)
   - Requires storing both response message IDs and comparison state

4. **Abort on streaming failure** ✓
   - If either response fails mid-stream, abort the entire comparison
   - Show error message and fall back to single-model mode for that turn
   - Clean up any partial database records
   - User can retry or continue with single response

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli/templates/base-init.sql` | Add `ab_comparisons` table |
| `src/utils/sql.py` | Add SQL queries for A/B operations |
| `src/interfaces/chat_app/app.py` | Add endpoint, ChatWrapper methods |
| `src/interfaces/chat_app/static/chat.js` | A/B voting UI logic |
| `src/interfaces/chat_app/static/chat.css` | Side-by-side layout styles |
| `src/interfaces/chat_app/templates/index.html` | (minimal changes, maybe add vote button template) |

---

## Estimated Effort

- Database migration: 1 hour
- Backend API: 3-4 hours
- Frontend logic: 4-5 hours
- CSS styling: 2-3 hours
- Testing & polish: 2-3 hours

**Total: ~12-16 hours**

---

## Risks & Mitigations

### Medium Risk

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Streaming failure leaves orphaned data** | One response stored but comparison aborted; inconsistent DB state | Medium | Clean up partial records on abort; use transaction where possible |
| **Anonymous display confuses users** | Users don't understand what Model A vs B means | Low | Add tooltip or help text: "We're comparing two different AI responses. Pick the one you prefer!" |
| **Warning modal fatigue** | Users dismiss warning without reading, then complain about 2x usage | Low | Keep warning concise; only show once per session or remember dismissal |

### Low Risk

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Mobile stacked layout less intuitive** | Harder to compare when responses aren't side-by-side | Low | Clear A/B labels; compact vote buttons between responses |
| **Conversation history ambiguity** | After voting, which response is "canonical" for context? | Low | Always use winning response (or A if tie) as canonical; store mapping in comparison record |

### Technical Debt Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No A/B analytics yet** | Data collected but no way to analyze it | Defer analytics dashboard to Phase 2; ensure schema supports future ELO calculations |
| **No cleanup of old comparison data** | Table grows unbounded | Add retention policy or archival strategy in future |
| **Frontend state complexity** | A/B state adds complexity to already-complex chat.js | Consider refactoring to more modular state management in future |

---

## Implementation Plan

### Phase 1: Database Schema (1 hour)

**Files:** `src/cli/templates/base-init.sql`, `src/utils/sql.py`

1. Add `ab_comparisons` table to `base-init.sql`
2. Add `is_config_a` boolean column to track randomized assignment
3. Add SQL query constants to `sql.py`:
   - `SQL_INSERT_AB_COMPARISON`
   - `SQL_UPDATE_AB_PREFERENCE`
   - `SQL_GET_AB_COMPARISON_BY_CONVERSATION`
   - `SQL_GET_PENDING_AB_COMPARISON`
   - `SQL_DELETE_AB_COMPARISON`

**Deliverable:** Migration SQL that can be applied to existing deployments

---

### Phase 2: Backend API (3-4 hours)

**Files:** `src/interfaces/chat_app/app.py`

#### 2.1 ChatWrapper Methods

```python
def create_ab_comparison(self, conversation_id, user_prompt_mid, 
                         response_a_mid, response_b_mid,
                         config_a_id, config_b_id, is_config_a_first: bool) -> int:
    """Create A/B comparison record. Returns comparison_id."""

def update_ab_preference(self, comparison_id, preference: str) -> None:
    """Record user's preference ('a', 'b', or 'tie')."""

def get_pending_ab_comparison(self, conversation_id) -> Optional[dict]:
    """Get incomplete A/B comparison for a conversation (if any)."""

def delete_ab_comparison(self, comparison_id) -> None:
    """Clean up aborted comparison."""
```

#### 2.2 New Endpoint: `POST /api/ab/preference`

```python
def submit_ab_preference(self):
    """Record user's A/B preference vote."""
    data = request.json
    comparison_id = data.get('comparison_id')
    preference = data.get('preference')  # 'a', 'b', or 'tie'
    client_id = data.get('client_id')
    
    # Validate
    if preference not in ('a', 'b', 'tie'):
        return jsonify({'error': 'Invalid preference'}), 400
    
    # Update database
    self.chat.update_ab_preference(comparison_id, preference)
    
    return jsonify({'success': True, 'comparison_id': comparison_id}), 200
```

#### 2.3 New Endpoint: `GET /api/ab/pending`

```python
def get_pending_ab_comparison(self):
    """Check if conversation has pending A/B comparison."""
    conversation_id = request.args.get('conversation_id')
    client_id = request.args.get('client_id')
    
    comparison = self.chat.get_pending_ab_comparison(conversation_id)
    return jsonify({'comparison': comparison}), 200
```

#### 2.4 Modify Streaming Response

Update `get_chat_response_streaming()` to accept optional A/B parameters:
- `is_ab_mode`: boolean
- `ab_role`: 'a' or 'b'
- `ab_comparison_id`: if response B, include existing comparison_id

Return `ab_metadata` in final event when A/B mode.

**Deliverable:** Working API endpoints, tested via curl

---

### Phase 3: Frontend - Core Logic (4-5 hours)

**Files:** `src/interfaces/chat_app/static/chat.js`

#### 3.1 State Management

```javascript
const Chat = {
  state: {
    // ... existing
    activeABComparison: null,  // { comparisonId, responseAId, responseBId, configAId, configBId }
    abVotePending: false,       // true when waiting for user vote
  },
};
```

#### 3.2 A/B Mode Warning Modal

Show modal when user enables A/B toggle:
- "A/B Testing Mode"
- "This will generate two responses per message, using 2x API calls."
- "You must vote on which response is better before continuing."
- [Enable] [Cancel]

#### 3.3 Modified `sendMessage()`

```javascript
async sendMessage() {
  // Block if vote pending
  if (this.state.abVotePending) {
    UI.showToast('Please vote on the current comparison first');
    return;
  }
  
  const isAB = UI.isABEnabled();
  
  if (isAB) {
    await this.sendABMessage();
  } else {
    await this.sendSingleMessage();
  }
}
```

#### 3.4 New `sendABMessage()`

```javascript
async sendABMessage() {
  // Randomize which config is A vs B
  const configs = [UI.getSelectedConfig('A'), UI.getSelectedConfig('B')];
  const shuffled = Math.random() < 0.5;
  const [configA, configB] = shuffled ? [configs[1], configs[0]] : configs;
  
  // Create side-by-side container
  UI.addABComparisonContainer();
  
  // Stream both responses in parallel
  const [resultA, resultB] = await Promise.all([
    this.streamABResponse('a', configA),
    this.streamABResponse('b', configB),
  ]);
  
  // Check for failures
  if (resultA.error || resultB.error) {
    UI.removeABComparisonContainer();
    UI.showError('A/B comparison failed. Falling back to single response.');
    // Clean up and retry single
    return;
  }
  
  // Create comparison record
  const comparison = await API.createABComparison({
    conversation_id: this.state.conversationId,
    user_prompt_mid: resultA.userMessageId,
    response_a_mid: resultA.messageId,
    response_b_mid: resultB.messageId,
    config_a_id: resultA.configId,
    config_b_id: resultB.configId,
    is_config_a_first: !shuffled,
  });
  
  // Show vote buttons
  this.state.activeABComparison = comparison;
  this.state.abVotePending = true;
  UI.showABVoteButtons(comparison.comparisonId);
  UI.setInputDisabled(true);
}
```

#### 3.5 New `submitABPreference()`

```javascript
async submitABPreference(preference) {
  await API.submitABPreference({
    comparison_id: this.state.activeABComparison.comparisonId,
    preference: preference,
    client_id: this.clientId,
  });
  
  // Update UI
  UI.markABWinner(preference);
  UI.hideABVoteButtons();
  
  // Collapse to canonical response
  const canonicalId = preference === 'b' 
    ? this.state.activeABComparison.responseBId 
    : this.state.activeABComparison.responseAId;
  UI.collapseABToCanonical(canonicalId, preference);
  
  // Clear state
  this.state.activeABComparison = null;
  this.state.abVotePending = false;
  UI.setInputDisabled(false);
}
```

#### 3.6 Conversation Load with Pending Comparison

```javascript
async loadConversation(conversationId) {
  // ... existing load logic
  
  // Check for pending A/B comparison
  if (UI.isABEnabled()) {
    const pending = await API.getPendingABComparison(conversationId);
    if (pending) {
      this.state.activeABComparison = pending;
      this.state.abVotePending = true;
      UI.restoreABComparisonUI(pending);
      UI.setInputDisabled(true);
    }
  }
}
```

**Deliverable:** Functional A/B voting flow

---

### Phase 4: Frontend - UI Components (2-3 hours)

**Files:** `src/interfaces/chat_app/static/chat.js`, `src/interfaces/chat_app/templates/index.html`

#### 4.1 UI Methods to Add

```javascript
const UI = {
  // ... existing
  
  addABComparisonContainer() {
    // Create side-by-side wrapper
  },
  
  showABVoteButtons(comparisonId) {
    // Add vote buttons below comparison
  },
  
  hideABVoteButtons() {
    // Remove vote buttons
  },
  
  markABWinner(preference) {
    // Highlight winning response, fade other
  },
  
  collapseABToCanonical(messageId, preference) {
    // Animate collapse, keep only winning response in flow
  },
  
  restoreABComparisonUI(comparison) {
    // Rebuild comparison UI from loaded conversation
  },
  
  showABWarningModal(onConfirm, onCancel) {
    // Warning modal for enabling A/B mode
  },
};
```

#### 4.2 HTML Templates

Add to `index.html`:
- A/B warning modal structure
- Vote button template (can be dynamically created)

**Deliverable:** Complete UI components

---

### Phase 5: Styling (2-3 hours)

**Files:** `src/interfaces/chat_app/static/chat.css`

#### 5.1 A/B Comparison Container

```css
.ab-comparison {
  display: flex;
  gap: 16px;
  margin: 16px 0;
}

.ab-response {
  flex: 1;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  max-height: 500px;
  overflow-y: auto;
}

.ab-response-header {
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-secondary);
}

/* Mobile: stack vertically */
@media (max-width: 768px) {
  .ab-comparison {
    flex-direction: column;
  }
}
```

#### 5.2 Vote Buttons

```css
.ab-vote-container {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin: 16px 0;
}

.ab-vote-btn {
  padding: 8px 24px;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.ab-vote-btn:hover {
  background: var(--accent-color);
  color: white;
}

.ab-vote-btn--tie {
  background: transparent;
}
```

#### 5.3 Winner/Loser States

```css
.ab-response--winner {
  border-color: var(--success-color);
  background: var(--success-bg);
}

.ab-response--loser {
  opacity: 0.6;
}

.ab-winner-badge {
  display: inline-block;
  background: var(--success-color);
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-left: 8px;
}
```

#### 5.4 Warning Modal

```css
.ab-warning-modal {
  /* Similar to existing settings modal */
}
```

**Deliverable:** Polished, responsive UI

---

### Phase 6: Integration & Testing (2-3 hours)

1. **Manual testing checklist:**
   - [ ] Enable A/B mode shows warning modal
   - [ ] Two responses stream side-by-side
   - [ ] Input disabled until vote
   - [ ] Vote buttons work (A, B, Tie)
   - [ ] Winner highlighted, loser faded
   - [ ] Comparison collapses to canonical response
   - [ ] Can continue chatting after vote
   - [ ] Reload conversation with pending comparison restores UI
   - [ ] Streaming failure aborts cleanly
   - [ ] Disable A/B mode during pending comparison
   - [ ] Mobile layout (stacked)
   - [ ] Database records created correctly

2. **Edge cases:**
   - [ ] Very long responses (scroll works)
   - [ ] Empty responses
   - [ ] Network disconnect during stream
   - [ ] Refresh page during streaming

**Deliverable:** Tested, working feature

---

### Implementation Order

```
┌─────────────────────────────────────────────────────────────────┐
│ Week 1                                                          │
├─────────────────────────────────────────────────────────────────┤
│ Day 1: Phase 1 (DB) + Phase 2 (Backend API)                     │
│ Day 2: Phase 3 (Frontend Logic - Core)                          │
│ Day 3: Phase 3 (Frontend Logic - Completion) + Phase 4 (UI)     │
│ Day 4: Phase 5 (Styling) + Phase 6 (Testing)                    │
│ Day 5: Bug fixes, polish, documentation                         │
└─────────────────────────────────────────────────────────────────┘
```

---

### Definition of Done

- [ ] Database migration applied successfully
- [ ] All API endpoints functional and documented
- [ ] Frontend A/B flow complete with voting
- [ ] Responsive design (desktop side-by-side, mobile stacked)
- [ ] Manual testing checklist passed
- [ ] Code reviewed and merged
- [ ] Deployed to staging environment
