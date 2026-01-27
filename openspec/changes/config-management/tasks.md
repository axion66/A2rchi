# Tasks: Config Management

> **Dependency**: Requires auth-system to be implemented first (for @admin_required, user identity)

## Phase 1: Schema Updates

- [ ] 1.1 Add new columns to dynamic_config table (prompts, top_p, top_k, etc.)
- [ ] 1.2 Add prompts_path to static_config table
- [ ] 1.3 Add user preference columns to users table
- [ ] 1.4 Create config_audit table
- [ ] 1.5 Update init-v2.sql template with new schema

## Phase 2: Prompt File System

- [ ] 2.1 Create prompts directory structure in templates
- [ ] 2.2 Create default prompt files (condense/default.prompt, chat/default.prompt, system/default.prompt)
- [ ] 2.3 Implement PromptService class
- [ ] 2.4 Implement prompt caching and reload
- [ ] 2.5 Write tests for PromptService

## Phase 3: Model Registry

- [ ] 3.1 Create `src/a2rchi/models/registry.py`
- [ ] 3.2 Register all existing model classes (OpenAILLM, AnthropicLLM, etc.)
- [ ] 3.3 Register all embedding classes
- [ ] 3.4 Write tests for ModelRegistry

## Phase 4: ConfigService Enhancement

- [ ] 4.1 Add `get_effective(field, user_id)` method
- [ ] 4.2 Add user preferences methods
- [ ] 4.3 Add audit logging for dynamic config changes
- [ ] 4.4 Add `initialize_from_yaml()` method
- [ ] 4.5 Integrate PromptService into ConfigService
- [ ] 4.6 Write tests for ConfigService (requires PostgreSQL)

## Phase 5: API Endpoints

- [ ] 5.1 Create GET /api/v2/config/static endpoint
- [ ] 5.2 Create GET /api/v2/config/dynamic endpoint
- [ ] 5.3 Create PUT /api/v2/config/dynamic endpoint (admin only)
- [ ] 5.4 Create GET /api/v2/user/preferences endpoint
- [ ] 5.5 Create PUT /api/v2/user/preferences endpoint
- [ ] 5.6 Create GET /api/v2/prompts endpoint (list)
- [ ] 5.7 Create GET /api/v2/prompts/:type/:name endpoint
- [ ] 5.8 Create POST /api/v2/prompts/reload endpoint (admin only)
- [ ] 5.9 Write API integration tests

## Phase 6: Service Migration (Big Bang)

- [ ] 6.1 Create migration script to identify all config_loader imports
- [ ] 6.2 Update `src/a2rchi/a2rchi.py` to use ConfigService
- [ ] 6.3 Update `src/data_manager/data_manager.py` to use ConfigService
- [ ] 6.4 Update `src/bin/service_*.py` files to use ConfigService
- [ ] 6.5 Update `src/interfaces/chat_app/` to use ConfigService
- [ ] 6.6 Update `src/interfaces/grader_app/` to use ConfigService
- [ ] 6.7 Update all remaining files using config_loader
- [ ] 6.8 Delete `src/utils/config_loader.py`
- [ ] 6.9 Run full test suite

## Phase 7: CLI Updates

- [ ] 7.1 Update `a2rchi start` to call `initialize_from_yaml()`
- [ ] 7.2 Update templates to include prompts directory
- [ ] 7.3 Add prompts to deployment directory creation

## Phase 8: Documentation

- [ ] 8.1 Update API documentation
- [ ] 8.2 Update user guide with config management
- [ ] 8.3 Document prompt customization
- [ ] 8.4 Add admin guide for deployment settings
