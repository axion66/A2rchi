# Chat API Specification

## ADDED Requirements

### Requirement: Streaming Message Response
The system SHALL stream chat responses using Server-Sent Events (SSE) format.

#### Scenario: Successful streaming response
- **GIVEN** a valid conversation context
- **WHEN** user submits a message to `/api/get_chat_response_stream`
- **THEN** server streams events in order: tool events (optional), chunk events, done event
- **AND** each event is JSON formatted with a `type` field
- **AND** conversation_id is included in the response

#### Scenario: Streaming with agent tools
- **GIVEN** an agent-based pipeline
- **WHEN** agent invokes tools during response generation
- **THEN** server streams `tool_start` event with tool_name and tool_args
- **AND** server streams `tool_output` event with result (truncated if large)
- **AND** server streams `tool_end` event with status and duration_ms
- **AND** final answer streams as `chunk` events

### Requirement: Agent Trace Retrieval
The system SHALL provide endpoints to retrieve agent execution traces.

#### Scenario: Get trace by ID
- **GIVEN** a completed streaming request with trace_id
- **WHEN** client requests `/api/trace/<trace_id>`
- **THEN** server returns full trace including all events, timestamps, and status

#### Scenario: Get trace by message ID
- **GIVEN** a message_id from a completed response
- **WHEN** client requests `/api/trace/by_message/<message_id>`
- **THEN** server returns the associated trace

### Requirement: A/B Comparison Management
The system SHALL support creating and voting on A/B comparisons.

#### Scenario: Create A/B comparison
- **GIVEN** A/B testing mode is enabled
- **WHEN** user sends a message with two model configurations
- **THEN** server creates ab_comparison record with both response IDs
- **AND** returns comparison_id to client

#### Scenario: Record preference vote
- **GIVEN** an active A/B comparison
- **WHEN** user selects preferred response (A, B, or tie)
- **THEN** server updates ab_comparison with preference and timestamp
- **AND** returns success confirmation

### Requirement: Conversation CRUD Operations
The system SHALL persist conversation history.

#### Scenario: Create new conversation
- **GIVEN** user starts a new chat
- **WHEN** first message is sent
- **THEN** server creates conversation_metadata record
- **AND** returns conversation_id for subsequent messages

#### Scenario: Load conversation history
- **GIVEN** an existing conversation_id
- **WHEN** client requests `/api/load_conversation`
- **THEN** server returns all messages in order
- **AND** includes feedback status for each message

#### Scenario: List user conversations
- **GIVEN** a client_id
- **WHEN** client requests `/api/list_conversations`
- **THEN** server returns conversations ordered by last_message_at
- **AND** includes title, created_at, and last_message_at

### Requirement: Stream Cancellation
The system SHALL support cancelling active streaming requests.

#### Scenario: Cancel streaming request
- **GIVEN** an active streaming response
- **WHEN** client sends cancel request to `/api/cancel_stream`
- **THEN** server marks trace as cancelled
- **AND** stops generating further events
- **AND** client receives cancellation confirmation

## Event Type Reference

| Event Type | Fields | Description |
|------------|--------|-------------|
| `chunk` | content, conversation_id | Text content fragment |
| `tool_start` | tool_call_id, tool_name, tool_args, timestamp | Tool invocation begins |
| `tool_output` | tool_call_id, output, truncated, full_length | Tool result |
| `tool_end` | tool_call_id, status, duration_ms | Tool invocation completes |
| `error` | status, message | Error occurred |
| `done` | conversation_id, message_id, trace_id | Streaming complete |
