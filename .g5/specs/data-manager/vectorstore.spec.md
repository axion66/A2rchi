---
type: spec
module: data_manager.vectorstore.manager
version: "1.0"
status: extracted
test_file: tests/unit/test_vectorstore.py
source_files:
  - src/data_manager/vectorstore/manager.py
  - src/data_manager/vectorstore/loader_utils.py
---

# VectorStore Manager Spec

## Overview

Manages ChromaDB vector store operations including document loading, embedding, and collection management.

## Dependencies

- `chromadb` - Vector database
- `langchain_community.document_loaders` - Document loaders
- `langchain_text_splitters` - Text chunking
- `src/data_manager/collectors/utils/index_utils.CatalogService`

## Public API

### Classes

#### `VectorStoreManager`
```python
class VectorStoreManager:
    """Encapsulates vectorstore configuration and synchronization."""
    
    config: Dict
    global_config: Dict
    data_path: str
    
    # Derived settings
    collection_name: str
    distance_metric: str  # "l2", "cosine", "ip"
    embedding_model: Any
    text_splitter: CharacterTextSplitter
    stemmer: Optional[PorterStemmer]
    parallel_workers: int
```

**Constructor:**
```python
def __init__(self, *, config: Dict, global_config: Dict, data_path: str) -> None
```

**Contracts:**
- REQUIRES: `distance_metric` in `["l2", "cosine", "ip"]`
- ENSURES: Collection name includes embedding name
- ENSURES: Initializes embedding model from class map
- ENSURES: Configures text splitter with chunk settings
- ENSURES: Initializes stemmer if enabled

**Methods:**

##### `delete_existing_collection_if_reset`
```python
def delete_existing_collection_if_reset(self) -> None
```
Delete collection if `reset_collection=True`.

**Contracts:**
- ENSURES: Only deletes if config flag set
- ENSURES: Checks collection exists before delete

##### `fetch_collection`
```python
def fetch_collection(self) -> Collection
```
Return the active ChromaDB collection.

**Contracts:**
- ENSURES: Creates collection if not exists
- ENSURES: Sets distance metric in metadata

##### `update_vectorstore`
```python
def update_vectorstore(self) -> None
```
Sync documents from filesystem to vectorstore.

**Contracts:**
- ENSURES: Loads documents from data_path
- ENSURES: Splits into chunks
- ENSURES: Embeds and stores in ChromaDB
- ENSURES: Uses parallel workers for loading

##### `_build_client` (protected)
```python
def _build_client(self) -> chromadb.Client
```
Build ChromaDB client from config.

**Contracts:**
- ENSURES: Uses persistent storage at configured path
- ENSURES: Configures anonymized telemetry

## Document Loading

Uses `select_loader(file_path)` to choose appropriate loader:

| Extension | Loader |
|-----------|--------|
| `.html` | BSHTMLLoader |
| `.pdf` | PyPDFLoader |
| `.py` | PythonLoader |
| `.md` | UnstructuredMarkdownLoader |
| `.txt` | TextLoader |
| (other) | TextLoader |

## Configuration

```yaml
data_manager:
  collection_name: "my_docs"
  embedding_name: "openai"
  distance_metric: "cosine"
  chunk_size: 1000
  chunk_overlap: 200
  reset_collection: false
  parallel_workers: 8
  stemming:
    enabled: false
  embedding_class_map:
    openai:
      class: OpenAIEmbeddings
      kwargs:
        model: "text-embedding-3-small"
```

## Invariants

1. Collection name always includes embedding name suffix
2. Distance metric validated on construction
3. Parallel workers >= 1
4. Stemmer only initialized if enabled
