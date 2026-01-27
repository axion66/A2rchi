# BYOK (Bring Your Own Key) Specification

## ADDED Requirements

### Requirement: Key Source Hierarchy
The system SHALL resolve API keys using a defined precedence hierarchy where environment variables take highest priority, followed by Docker secrets, followed by session storage.

#### Scenario: Environment variable takes precedence
- **GIVEN** an environment variable `OPENAI_API_KEY` is set
- **AND** a session key for OpenAI is also stored
- **WHEN** a request is made using the OpenAI provider
- **THEN** the environment variable key SHALL be used
- **AND** the key source SHALL be reported as "env"

#### Scenario: Session key used when no env var
- **GIVEN** no environment variable for Anthropic is set
- **AND** a session key for Anthropic is stored
- **WHEN** a request is made using the Anthropic provider
- **THEN** the session key SHALL be used
- **AND** the key source SHALL be reported as "session"

#### Scenario: No key available
- **GIVEN** no environment variable for Gemini is set
- **AND** no session key for Gemini is stored
- **WHEN** a request is made using the Gemini provider
- **THEN** the request SHALL fail with a clear error message
- **AND** the key source SHALL be reported as null

---

### Requirement: Session Key Storage
The system SHALL provide secure session-based storage for user-provided API keys that persists across requests within the same session.

#### Scenario: Store session key
- **GIVEN** a user is authenticated with a valid session
- **WHEN** the user provides an API key via `POST /api/providers/keys/set`
- **THEN** the key SHALL be stored in the encrypted session
- **AND** the key SHALL be available for subsequent requests
- **AND** a success response SHALL be returned

#### Scenario: Session key persistence
- **GIVEN** a session key has been stored for OpenAI
- **WHEN** the user makes multiple chat requests in the same session
- **THEN** the same session key SHALL be used for all requests

#### Scenario: Clear session key
- **GIVEN** a session key is stored for Anthropic
- **WHEN** the user calls `POST /api/providers/keys/clear` with provider "anthropic"
- **THEN** the session key SHALL be removed
- **AND** subsequent requests SHALL require a new key

---

### Requirement: Key Status API
The system SHALL provide an API endpoint to retrieve the status of API keys for all enabled providers without exposing the actual key values.

#### Scenario: Get key status for all providers
- **WHEN** a user calls `GET /api/providers/keys`
- **THEN** the response SHALL include all enabled providers
- **AND** each provider SHALL include: id, name, has_key (boolean), source (string or null)
- **AND** the actual key values SHALL NOT be included

#### Scenario: Key status shows correct source
- **GIVEN** OpenAI has an environment variable key
- **AND** Anthropic has a session key
- **AND** Gemini has no key
- **WHEN** the user calls `GET /api/providers/keys`
- **THEN** OpenAI SHALL show source "env" and has_key true
- **AND** Anthropic SHALL show source "session" and has_key true  
- **AND** Gemini SHALL show source null and has_key false

---

### Requirement: Key Security
The system SHALL protect API keys from exposure through logging, API responses, or client-side storage.

#### Scenario: Keys not logged
- **WHEN** an API key operation occurs (set, clear, use)
- **THEN** the key value SHALL NOT appear in any log output
- **AND** only the operation type and provider SHALL be logged

#### Scenario: Keys not echoed in responses
- **WHEN** a key is set via `POST /api/providers/keys/set`
- **THEN** the response SHALL NOT include the key value
- **AND** only the success status and source SHALL be returned

#### Scenario: Keys masked in UI
- **WHEN** a user views the API Keys section in Settings
- **AND** a key is configured (from any source)
- **THEN** the input field SHALL display masked characters (e.g., "••••••••")
- **AND** the actual key value SHALL NOT be visible

---

### Requirement: UI Key Management
The system SHALL provide a user interface for viewing key status and managing session keys within the Settings modal.

#### Scenario: Display key status
- **WHEN** a user opens the Settings modal
- **AND** expands the API Keys section
- **THEN** all enabled providers SHALL be listed
- **AND** each provider SHALL show its key status indicator

#### Scenario: Status indicator for env key
- **GIVEN** a provider has a key from environment variable
- **WHEN** displayed in the UI
- **THEN** a "✓ ENV" indicator SHALL be shown in green
- **AND** the input field SHALL be disabled

#### Scenario: Status indicator for session key
- **GIVEN** a provider has a key from session
- **WHEN** displayed in the UI
- **THEN** a "✓ SET" indicator SHALL be shown in blue
- **AND** a "Clear" button SHALL be available

#### Scenario: Status indicator for no key
- **GIVEN** a provider has no key configured
- **WHEN** displayed in the UI
- **THEN** a "○" indicator SHALL be shown in gray
- **AND** a "Set" button SHALL be available

#### Scenario: Set session key from UI
- **GIVEN** a provider has no environment variable key
- **WHEN** the user enters a key in the input field
- **AND** clicks the "Set" button
- **THEN** the key SHALL be sent to the server
- **AND** the UI SHALL update to show the new status

#### Scenario: Clear session key from UI
- **GIVEN** a provider has a session key
- **WHEN** the user clicks the "Clear" button
- **THEN** the session key SHALL be removed
- **AND** the UI SHALL update to show no key status

---

### Requirement: Provider Key Integration
The system SHALL support runtime API key injection for all provider implementations.

#### Scenario: Use injected key for chat
- **GIVEN** a session key is stored for a provider
- **WHEN** the user sends a chat message with that provider selected
- **THEN** the provider SHALL use the injected key
- **AND** the chat response SHALL be generated successfully

#### Scenario: Key injection does not affect env keys
- **GIVEN** an environment variable key is configured
- **WHEN** a session key is also set for the same provider
- **THEN** the environment variable key SHALL be used for requests
- **AND** the session key SHALL be ignored

---

### Requirement: Collapsible API Keys Section
The system SHALL display the API Keys section in a collapsible format to reduce UI clutter when key management is not needed.

#### Scenario: Default collapsed state
- **GIVEN** all enabled providers have environment variable keys
- **WHEN** the user opens the Settings modal
- **THEN** the API Keys section SHALL be collapsed by default

#### Scenario: Toggle expansion
- **WHEN** the user clicks the API Keys section header
- **THEN** the section SHALL toggle between expanded and collapsed states
- **AND** a visual indicator (chevron) SHALL show the current state

#### Scenario: Expanded when keys needed
- **GIVEN** at least one provider has no key configured
- **WHEN** the user opens the Settings modal
- **THEN** the API Keys section MAY be expanded by default
