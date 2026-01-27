# Multi-Provider Model Support - Tasks

## Phase 1: Provider Abstraction (Backend)

### 1.1 Create Provider Base Class
- [ ] Create `src/a2rchi/providers/__init__.py`
- [ ] Create `src/a2rchi/providers/base.py` with `BaseProvider` ABC
- [ ] Define `ModelInfo` dataclass (name, display_name, context_window, capabilities)
- [ ] Define `ProviderConfig` dataclass

### 1.2 Implement OpenAI Provider
- [ ] Create `src/a2rchi/providers/openai_provider.py`
- [ ] Extract OpenAI logic from existing `a2rchi.py`
- [ ] Implement `get_chat_model()`, `get_embeddings()`, `list_models()`
- [ ] Add connection validation

### 1.3 Provider Registry
- [ ] Create `src/a2rchi/providers/registry.py`
- [ ] Implement provider discovery and instantiation
- [ ] Add `get_provider(name)` function
- [ ] Add `list_enabled_providers()` function

### 1.4 Update Config Schema
- [ ] Add `providers` section to config schema
- [ ] Update `config_loader.py` to parse provider configs
- [ ] Create example provider configuration

---

## Phase 2: Additional Providers (Backend)

### 2.1 Anthropic Provider
- [ ] Create `src/a2rchi/providers/anthropic_provider.py`
- [ ] Implement using `langchain-anthropic`
- [ ] Handle Claude-specific parameters (max_tokens required)
- [ ] Add model list (claude-sonnet-4, claude-3.5-haiku, etc.)

### 2.2 Gemini Provider
- [ ] Create `src/a2rchi/providers/gemini_provider.py`
- [ ] Implement using `langchain-google-genai`
- [ ] Handle Gemini-specific features
- [ ] Add model list (gemini-2.0-flash, gemini-1.5-pro, etc.)

### 2.3 OpenRouter Provider
- [ ] Create `src/a2rchi/providers/openrouter_provider.py`
- [ ] Implement using OpenAI-compatible API
- [ ] Dynamic model list from OpenRouter API
- [ ] Handle provider-specific headers

### 2.4 Local Server Provider
- [ ] Create `src/a2rchi/providers/local_provider.py`
- [ ] Support Ollama, vLLM, LocalAI APIs
- [ ] Configurable base URL
- [ ] Model discovery from local server

### 2.5 Provider Health Checks
- [ ] Add `validate_connection()` to each provider
- [ ] Implement graceful fallback on provider failure
- [ ] Add provider status API endpoint

---

## Phase 3: Agent Abstraction (Backend)

### 3.1 Create Agent Base Class
- [ ] Create `src/a2rchi/agents/__init__.py`
- [ ] Create `src/a2rchi/agents/base.py` with `BaseAgent` ABC
- [ ] Define `AgentConfig` dataclass
- [ ] Define `AgentCapabilities` (supports_tools, supports_streaming, etc.)

### 3.2 Refactor ReAct Agent
- [ ] Create `src/a2rchi/agents/react_agent.py`
- [ ] Extract existing agent logic from `a2rchi.py`
- [ ] Implement `BaseAgent` interface
- [ ] Decouple from specific provider

### 3.3 Create Simple Agent
- [ ] Create `src/a2rchi/agents/simple_agent.py`
- [ ] Direct chat without tool usage
- [ ] Simpler streaming implementation
- [ ] Good for quick responses or when tools not needed

### 3.4 Agent Registry
- [ ] Create `src/a2rchi/agents/registry.py`
- [ ] Load agent configs from YAML
- [ ] Support dynamic agent selection
- [ ] Validate agent-tool compatibility

---

## Phase 4: API Updates

### 4.1 Provider Endpoints
- [ ] Add `GET /api/providers` - list enabled providers with models
- [ ] Add `POST /api/set_provider` - set session provider
- [ ] Add `GET /api/provider_status` - check provider health

### 4.2 Agent Endpoints
- [ ] Add `GET /api/agents` - list available agents
- [ ] Add `POST /api/set_agent` - set session agent
- [ ] Add `GET /api/agent/{name}` - get agent details

### 4.3 Session Config
- [ ] Add `GET /api/session_config` - get current selections
- [ ] Store provider/model/agent selection in session
- [ ] Support per-conversation overrides

### 4.4 Update Streaming
- [ ] Modify `/api/get_chat_response_stream` to use selected provider
- [ ] Pass agent selection to streaming handler
- [ ] Handle provider-specific streaming differences

---

## Phase 5: Frontend Updates

### 5.1 Settings Modal - Provider Section
- [ ] Add "Model Provider" dropdown in Settings
- [ ] Add "Model" dropdown (filtered by provider)
- [ ] Show model info (context window, capabilities)
- [ ] Disable unavailable providers

### 5.2 Settings Modal - Agent Section
- [ ] Add "Agent" dropdown
- [ ] Show agent description
- [ ] Indicate tool support status
- [ ] Show recommended provider for each agent

### 5.3 Input Area Updates
- [ ] Show current provider + model in input footer
- [ ] Show current agent name
- [ ] Quick-switch dropdown (optional)
- [ ] Visual indicator for local vs cloud

### 5.4 State Management
- [ ] Store selection in localStorage
- [ ] Sync with server on load
- [ ] Handle provider becoming unavailable
- [ ] Preserve selection across sessions

### 5.5 A/B Testing Updates
- [ ] Allow selecting different providers for A vs B
- [ ] Show provider info in comparison cards
- [ ] Record provider in A/B comparison data

---

## Phase 6: Documentation & Testing

### 6.1 Configuration Documentation
- [ ] Document provider configuration options
- [ ] Document agent configuration options
- [ ] Add provider setup guides (API keys)
- [ ] Update quickstart guide

### 6.2 Provider Guides
- [ ] OpenAI setup guide
- [ ] Anthropic setup guide
- [ ] Gemini setup guide
- [ ] OpenRouter setup guide
- [ ] Local LLM setup guide (Ollama)

### 6.3 Testing
- [ ] Unit tests for each provider
- [ ] Unit tests for each agent type
- [ ] Integration tests for provider switching
- [ ] Smoke tests for UI provider selector

---

## Dependencies to Add

```
# pyproject.toml additions
langchain-anthropic>=0.2.0
langchain-google-genai>=2.0.0
```

---

## Migration Notes

1. Existing configs should continue to work (backwards compatible)
2. Default to OpenAI provider if no provider config specified
3. Existing agent behavior preserved with "react" agent type
