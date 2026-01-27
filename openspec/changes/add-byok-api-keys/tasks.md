# BYOK Implementation Tasks

## 1. Backend - Provider Key Infrastructure
- [x] 1.1 Add `set_api_key()` method to BaseProvider class
- [x] 1.2 Add `api_key` property setter for runtime key injection
- [x] 1.3 Create `get_provider_with_api_key()` factory function
- [x] 1.4 Create `get_chat_model_with_api_key()` helper function

## 2. Backend - API Endpoints
- [x] 2.1 Implement `GET /api/providers/keys` endpoint
- [x] 2.2 Implement `POST /api/providers/keys/set` endpoint  
- [x] 2.3 Implement `POST /api/providers/keys/clear` endpoint
- [x] 2.4 Implement `POST /api/providers/keys/validate` endpoint (optional)
- [x] 2.5 Add session key storage with Flask sessions
- [x] 2.6 Implement key source detection (env vs session)

## 3. Backend - Stream Integration
- [x] 3.1 Modify `get_chat_response_stream()` to accept API key parameter
- [x] 3.2 Add `_create_provider_llm()` helper with key injection
- [x] 3.3 Update stream endpoint to pass provider API key

## 4. Frontend - API Key UI
- [x] 4.1 Add API key status display in Settings modal
- [x] 4.2 Implement key input fields with masking
- [x] 4.3 Add Set/Clear buttons with appropriate visibility
- [x] 4.4 Show key source indicators (ENV/SET/none)
- [x] 4.5 Make API Keys section collapsible
- [x] 4.6 Add info text explaining key precedence

## 5. Frontend - API Integration
- [x] 5.1 Implement `getProviderKeys()` API call
- [x] 5.2 Implement `setProviderKey()` API call
- [x] 5.3 Implement `clearProviderKey()` API call
- [x] 5.4 Add loading states during key operations
- [x] 5.5 Add error handling and user feedback

## 6. Security Hardening
- [x] 6.1 Ensure API keys never logged
- [x] 6.2 Verify keys not returned in full from any endpoint
- [x] 6.3 Add input validation for key format
- [x] 6.4 Verify session cookies are Secure and HttpOnly

## 7. Documentation
- [x] 7.1 Update user guide with BYOK instructions
- [x] 7.2 Document key hierarchy and precedence
- [x] 7.3 Add deployment guide for HTTPS requirements
- [x] 7.4 Document configuration options for admins

## 8. Testing
- [x] 8.1 Test key hierarchy (env takes precedence)
- [x] 8.2 Test session key persistence across requests
- [x] 8.3 Test session key cleared on clear action
- [x] 8.4 Test UI updates correctly on key changes
- [x] 8.5 Test disabled state for env-configured providers

## 9. Validation
- [x] 9.1 Unit tests passing (15/15 tests)
- [x] 9.2 Browser testing - Settings modal API Keys section
- [x] 9.3 Browser testing - Save key shows ✓ SESSION indicator
- [x] 9.4 Browser testing - Clear key with confirmation dialog
- [x] 9.5 Screenshot saved to docs/_static/byok-settings.png
