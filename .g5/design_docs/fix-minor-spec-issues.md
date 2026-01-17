# Design Doc: Fix Minor Spec Issues

## Overview
Fix all 12 minor spec-code discrepancies identified during verification.

## Goals
- Fix all minor spec issues from verification task
- Achieve 100% spec-code match rate

## Scope
- Fix method/function naming differences
- Fix parameter naming differences  
- Fix class field mismatches
- Update verification document

## Changes Made

| Spec | Issue | Fix |
|------|-------|-----|
| a2rchi/core.spec.md | Constructor signature | Removed `config_name` from positional |
| cli/utilities.spec.md | `assign_feedback_palette` signature | Fixed to `(configs: List[Dict]) -> List[Dict]` |
| data-manager/collectors.spec.md | `ResourceMetadata` fields | Simplified to `display_name` + `extra` |
| data-manager/scrapers.spec.md | Method name | `scrape` → `crawl` |
| data-manager/tickets.spec.md | `TicketResource` fields | Simplified to match dataclass |
| interfaces/chat-utils.spec.md | Function name | `validate_login` → `check_credentials` |
| models/vllm.spec.md | SamplingParams | Removed unused `seed` param |
| pipelines/base.spec.md | Retriever attribute | Clarified not set in `__init__` |
| pipelines/prompt-utils.spec.md | INPUT_KEYS | Fixed to actual 5 variables |
| pipelines/safety.spec.md | Parameter name | `context` → `text_type` |

## Result
All 40 specs now match their source code (100% MATCH).
