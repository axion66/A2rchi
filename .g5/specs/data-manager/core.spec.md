---
type: spec
module: data_manager.data_manager
version: "1.0"
status: extracted
test_file: tests/unit/test_data_manager.py
source_files:
  - src/data_manager/data_manager.py
---

# Data Manager Core Spec

## Overview

Main orchestrator that coordinates data collection from various sources and manages the vector store. Initializes collectors, persistence, and vectorstore on construction.

## Dependencies

- `src/data_manager/collectors/persistence.PersistenceService`
- `src/data_manager/collectors/scrapers/scraper_manager.ScraperManager`
- `src/data_manager/collectors/tickets/ticket_manager.TicketManager`
- `src/data_manager/vectorstore/manager.VectorStoreManager`
- `src/utils/config_loader.load_config`

## Public API

### Classes

#### `DataManager`
```python
class DataManager:
    """Orchestrates data collection and vector store management."""
    
    # Configuration
    config: Dict
    global_config: Dict
    data_path: str
    
    # Services
    persistence: PersistenceService
    vector_manager: VectorStoreManager
    
    # Vectorstore properties (proxied from vector_manager)
    collection_name: str
    distance_metric: str
    embedding_model: Any
    text_splitter: Any
    stemmer: Optional[Any]
```

**Constructor:**
```python
def __init__(self) -> None
```

**Contracts:**
- ENSURES: Creates `data_path` directory if not exists
- ENSURES: Initializes `PersistenceService`
- ENSURES: Runs all collectors in sequence (scrapers, tickets)
- ENSURES: Flushes persistence index after collection
- ENSURES: Initializes `VectorStoreManager`
- ENSURES: Deletes existing collection if reset configured
- ENSURES: Updates vectorstore with collected documents

**Initialization Sequence:**
```
1. Load config
2. Create data_path directory
3. Initialize PersistenceService
4. Run ScraperManager.collect()
5. Run TicketManager.collect()
6. Flush persistence index
7. Initialize VectorStoreManager
8. Reset collection if configured
9. Update vectorstore
```

**Methods:**

##### `delete_existing_collection_if_reset`
```python
def delete_existing_collection_if_reset(self) -> None
```
Proxy to `vector_manager.delete_existing_collection_if_reset()`.

##### `fetch_collection`
```python
def fetch_collection(self) -> Collection
```
Proxy to `vector_manager.fetch_collection()`.

##### `update_vectorstore`
```python
def update_vectorstore(self) -> None
```
Proxy to `vector_manager.update_vectorstore()`.

## Configuration Schema

```yaml
global:
  DATA_PATH: "/path/to/data"
data_manager:
  collection_name: "my_collection"
  embedding_name: "openai"
  distance_metric: "cosine"
  # ... more settings
```

## Invariants

1. All collectors run synchronously in defined order
2. Persistence is flushed before vectorstore operations
3. Collection reset happens before update
4. All vectorstore properties are proxied from VectorStoreManager
