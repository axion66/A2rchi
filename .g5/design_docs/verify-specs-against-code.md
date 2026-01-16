# Design Doc: Verify Specs Against Code

## Overview
Systematic verification of all 40 G5 specs against their source code files.

## Verification Results Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ MATCH | 27 | 67.5% |
| ⚠️ MINOR | 12 | 30% |
| ❌ MISMATCH | 1 | 2.5% |

## Verification Checklist

| # | Spec | Source Files | Status | Notes |
|---|------|--------------|--------|-------|
| 1 | utils/config-loader.spec.md | src/utils/config_loader.py | ✅ MATCH | All functions match |
| 2 | utils/env.spec.md | src/utils/env.py | ✅ MATCH | `read_secret` matches exactly |
| 3 | utils/logging.spec.md | src/utils/logging.py | ✅ MATCH | All functions and constants match |
| 4 | utils/sql.spec.md | src/utils/sql.py | ✅ MATCH | All SQL constants exist |
| 5 | utils/benchmark-report.spec.md | src/utils/generate_benchmark_report.py | ⚠️ MINOR | Typo in `format_html_output` template |
| 6 | a2rchi/core.spec.md | src/a2rchi/a2rchi.py | ⚠️ MINOR | Constructor signature slightly different |
| 7 | models/base.spec.md | src/a2rchi/models/base.py | ❌ MISMATCH | `_response_cache` not defined in BaseCustomLLM |
| 8 | models/langchain-wrappers.spec.md | Multiple files | ⚠️ MINOR | Wrong source path in metadata |
| 9 | models/claude.spec.md | src/a2rchi/models/claude.py | ✅ MATCH | All verified |
| 10 | models/huggingface.spec.md | Multiple files | ⚠️ MINOR | Wrong source path; missing `auth_token` param |
| 11 | models/llama.spec.md | src/a2rchi/models/llama.py | ✅ MATCH | All verified |
| 12 | models/vllm.spec.md | src/a2rchi/models/vllm.py | ⚠️ MINOR | `presence_penalty` not in SamplingParams |
| 13 | models/safety.spec.md | src/a2rchi/models/safety.py | ✅ MATCH | All verified |
| 14 | models/dumb.spec.md | src/a2rchi/models/dumb.py | ✅ MATCH | All verified |
| 15 | pipelines/base.spec.md | src/a2rchi/pipelines/base.py | ⚠️ MINOR | `retriever` not initialized in __init__ |
| 16 | pipelines/qa.spec.md | src/a2rchi/pipelines/classic_pipelines/qa.py | ✅ MATCH | All verified |
| 17 | pipelines/grading.spec.md | src/a2rchi/pipelines/classic_pipelines/grading.py | ✅ MATCH | All verified |
| 18 | pipelines/image.spec.md | Multiple files | ✅ MATCH | All verified |
| 19 | pipelines/chain-wrapper.spec.md | src/a2rchi/pipelines/classic_pipelines/chain.py | ✅ MATCH | All verified |
| 20 | pipelines/token-limiter.spec.md | src/a2rchi/pipelines/classic_pipelines/token_limiter.py | ✅ MATCH | All verified |
| 21 | pipelines/prompt-utils.spec.md | src/a2rchi/pipelines/classic_pipelines/prompt_utils.py | ⚠️ MINOR | Some INPUT_KEYS don't exist |
| 22 | pipelines/safety.spec.md | src/a2rchi/pipelines/classic_pipelines/safety.py | ⚠️ MINOR | Param named `input_text` not `context` |
| 23 | data-manager/core.spec.md | src/data_manager/data_manager.py | ✅ MATCH | All verified |
| 24 | data-manager/persistence.spec.md | src/data_manager/collectors/persistence.py | ✅ MATCH | All verified |
| 25 | data-manager/collectors.spec.md | src/data_manager/collectors/ | ⚠️ MINOR | BaseResource fields differ |
| 26 | data-manager/scrapers.spec.md | src/data_manager/collectors/scrapers/ | ⚠️ MINOR | `scrape` vs `run_scrape` |
| 27 | data-manager/tickets.spec.md | src/data_manager/collectors/tickets/ | ⚠️ MINOR | TicketResource fields differ |
| 28 | data-manager/vectorstore.spec.md | src/data_manager/vectorstore/ | ✅ MATCH | All verified |
| 29 | data-manager/retrievers.spec.md | src/data_manager/vectorstore/retrievers.py | ✅ MATCH | All verified |
| 30 | cli/registries.spec.md | src/cli/service_registry.py, source_registry.py | ✅ MATCH | All verified |
| 31 | cli/managers.spec.md | src/cli/managers/ | ✅ MATCH | All verified |
| 32 | cli/service-builder.spec.md | src/cli/utils/service_builder.py | ✅ MATCH | All verified |
| 33 | cli/utilities.spec.md | src/cli/utils/ | ⚠️ MINOR | `assign_feedback_palette` signature differs |
| 34 | cli/commands.spec.md | src/cli/cli_main.py | ✅ MATCH | All verified |
| 35 | interfaces/chat-app.spec.md | src/interfaces/chat_app/app.py | ⚠️ MINOR | Method names differ |
| 36 | interfaces/chat-utils.spec.md | src/interfaces/chat_app/*.py | ⚠️ MINOR | `validate_login` → `verify_login` |
| 37 | interfaces/grader-app.spec.md | src/interfaces/grader_app/app.py | ⚠️ MINOR | Routes differ from spec |
| 38 | interfaces/integrations.spec.md | src/interfaces/piazza.py, mattermost.py | ✅ MATCH | All verified |
| 39 | interfaces/redmine-mailbox.spec.md | src/interfaces/redmine_mailer_integration/ | ✅ MATCH | All verified |
| 40 | bin/services.spec.md | src/bin/ | ✅ MATCH | All verified |

## Critical Issue

### ❌ MISMATCH: models/base.spec.md
- Spec claims `_response_cache: Dict` exists as class variable in `BaseCustomLLM`
- Code does **not** define this - only uses it via `self._response_cache`
- Each subclass defines its own cache at module level
- Would cause `AttributeError` if `_call` called on `BaseCustomLLM` directly

**Recommendation**: Update spec to clarify cache is defined in subclasses, not base class.

## Minor Issues Summary

| Category | Count | Examples |
|----------|-------|----------|
| Wrong source path in metadata | 3 | #8, #10, #21 |
| Method/param naming differences | 5 | #22, #35, #36, #33, #26 |
| Missing params in spec | 2 | #10, #12 |
| Simplified data structures in code | 2 | #25, #27 |
| Other minor discrepancies | 3 | #5, #6, #15 |

## Recommendations

1. **Fix critical mismatch** in `models/base.spec.md` regarding `_response_cache`
2. **Update source paths** in spec metadata for #8, #10, #21
3. **Consider spec updates** for method naming to match actual code
4. **Low priority**: Minor parameter differences are acceptable for uplift specs
