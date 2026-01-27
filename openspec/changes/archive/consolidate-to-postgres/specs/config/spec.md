## ADDED Requirements

### Requirement: Static Configuration
The system SHALL separate deploy-time configuration into a `static_config` table that is loaded once at startup and immutable at runtime.

#### Scenario: Static config loading at startup
- **WHEN** the application starts
- **THEN** static configuration is loaded from config.yaml
- **AND** stored in the `static_config` table (single row)
- **AND** cached in memory for fast access

#### Scenario: Static config immutability
- **WHEN** an attempt is made to modify static config at runtime
- **THEN** the modification is rejected
- **AND** an error indicates that restart/redeployment is required

#### Scenario: Embedding model in static config
- **WHEN** embedding_model is specified in config.yaml
- **THEN** it is stored in static_config.embedding_model
- **AND** changing it requires re-indexing all documents (documented as breaking change)

**Static configuration fields:**
- deployment_name, config_version
- data_path
- embedding_model, embedding_dimensions
- chunk_size, chunk_overlap, distance_metric
- available_pipelines, available_models, available_providers
- auth_enabled

---

### Requirement: Dynamic Configuration
The system SHALL support runtime-modifiable configuration in a `dynamic_config` table editable via API without restart.

#### Scenario: Dynamic config read
- **WHEN** the application needs current settings
- **THEN** it queries the `dynamic_config` table
- **AND** returns the active_pipeline, active_model, temperature, etc.

#### Scenario: Dynamic config update via API
- **WHEN** an admin updates dynamic config via `PUT /api/config/dynamic`
- **THEN** the `dynamic_config` table is updated
- **AND** `updated_at` and `updated_by` are set
- **AND** the change takes effect immediately without restart
- **AND** in-memory caches in all services are invalidated

#### Scenario: Dynamic config validation error
- **WHEN** invalid values are provided (e.g., temperature > 2.0, unknown model)
- **THEN** a 400 Bad Request response is returned
- **AND** error message indicates which field(s) failed validation
- **AND** no changes are made to the database

#### Scenario: Model selection validation
- **WHEN** setting active_model in dynamic config
- **THEN** the value must be in static_config.available_models
- **AND** invalid selections are rejected with an error

**Dynamic configuration fields:**
- active_pipeline, active_model
- temperature, max_tokens, system_prompt
- num_documents_to_retrieve
- use_hybrid_search, bm25_weight, semantic_weight

---

### Requirement: Config API Endpoints
The system SHALL provide REST API endpoints for configuration management.

#### Scenario: GET static config
- **WHEN** `GET /api/config/static` is called
- **THEN** the static configuration is returned as JSON
- **AND** sensitive fields (encryption keys) are excluded

#### Scenario: GET dynamic config
- **WHEN** `GET /api/config/dynamic` is called
- **THEN** the current dynamic configuration is returned as JSON

#### Scenario: PUT dynamic config (authorized)
- **WHEN** `PUT /api/config/dynamic` is called by an admin
- **THEN** the dynamic configuration is updated
- **AND** a success response is returned with the new values

#### Scenario: PUT dynamic config (unauthorized)
- **WHEN** `PUT /api/config/dynamic` is called by a non-admin user
- **THEN** a 403 Forbidden response is returned
- **AND** no changes are made

---

### Requirement: User Profile API
The system SHALL provide REST API endpoints for user profile and preferences.

#### Scenario: GET user profile
- **WHEN** `GET /api/user/profile` is called
- **THEN** the user's preferences are returned
- **AND** BYOK API key values are NOT returned (only presence indicators)

#### Scenario: PUT user profile
- **WHEN** `PUT /api/user/profile` is called with updated preferences
- **THEN** the user's preferences are updated in the database
- **AND** a success response is returned

---

## MODIFIED Requirements

### Requirement: ChromaDB Config Removal
The system SHALL remove ChromaDB configuration from config.yaml and replace it with PostgreSQL vectorstore settings.

#### Scenario: Config file migration
- **WHEN** existing deployments upgrade to the new version
- **THEN** `services.chromadb` config section is no longer required
- **AND** vectorstore settings move to `services.postgres.vectorstore`
- **AND** a clear migration guide documents the config changes

#### Scenario: Redmine/Mailer service config compatibility
- **WHEN** redmine_mailbox service loads configuration
- **THEN** `services.postgres` config is used (unchanged from current)
- **AND** no additional config changes are required for these services
- **AND** the services continue to work without modification

#### Scenario: VectorstoreConnector config migration
- **WHEN** VectorstoreConnector initializes
- **THEN** it reads `services.postgres.vectorstore` instead of `services.chromadb`
- **AND** fallback logic handles missing config gracefully during transition

#### Scenario: POST user API key
- **WHEN** `POST /api/user/api-keys/:provider` is called with a key
- **THEN** the key is encrypted and stored
- **AND** a success response indicates the key was saved

#### Scenario: DELETE user API key
- **WHEN** `DELETE /api/user/api-keys/:provider` is called
- **THEN** the encrypted key is removed
- **AND** a success response is returned
