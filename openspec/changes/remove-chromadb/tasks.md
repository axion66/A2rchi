# Tasks: Remove ChromaDB

## Phase 1: Core Code Changes

- [x] Update `src/data_manager/vectorstore/manager.py` to use PostgresVectorStore exclusively (already done)
- [x] Remove ChromaDB client initialization code from manager.py (already done - no chromadb code)
- [x] Update `src/a2rchi/utils/vectorstore_connector.py` if it references ChromaDB (N/A - uses manager)
- [x] Remove `enable_debug_chroma_endpoints` from API code (removed from base-config.yaml)

## Phase 2: CLI and Templates

- [x] Remove chromadb service from `src/cli/templates/base-compose.yaml` (not present)
- [x] Remove chromadb section from `src/cli/templates/base-config.yaml` (removed debug option)
- [x] Add postgres vectorstore config to base-config.yaml (already present)
- [x] Delete `src/cli/templates/dockerfiles/Dockerfile-chroma`
- [x] Update `src/cli/utils/service_builder.py` to not create chromadb service
- [x] Keep `src/cli/cli_main.py` migration commands for backwards compatibility

## Phase 3: Configuration Updates

- [x] Update `examples/deployments/basic-agent/config.yaml`
- [x] Update `examples/deployments/basic-gpu/config.yaml`
- [x] Update `examples/deployments/basic-ollama/config.yaml`
- [x] Update `examples/deployments/grading/config.yaml`
- [x] Update `examples/deployments/teaching_assistant/config.yaml`
- [x] Update `examples/benchmarking/benchmarking_configs/*.yaml`
- [x] Update `tests/pr_preview_config/pr_preview_config.yaml`

## Phase 4: Dependencies

- [x] chromadb remains optional in pyproject.toml for migration purposes
- [x] No chromadb in requirements-base.txt (confirmed)

## Phase 5: Documentation

- [x] Update `docs/docs/quickstart.md`
- [x] Update `docs/docs/advanced_setup_deploy.md`
- [x] Update `docs/docs/migration_guide.md` (kept migration commands for legacy users)
- [x] Update `docs/docs/api_reference.md`
- [x] Update `docs/docs/user_guide.md`

## Phase 6: Testing

- [ ] Run existing tests to verify nothing breaks
- [ ] Test new deployment without ChromaDB
- [ ] Verify vector search works with PostgresVectorStore

## Phase 7: Cleanup

- [x] Remove any remaining chromadb references (kept in migration code)
- [ ] Update existing deployment to remove chromadb container
- [ ] Archive this change proposal
