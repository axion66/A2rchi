---
type: spec
module: data_manager.collectors.persistence
version: "1.0"
status: extracted
test_file: tests/unit/test_persistence.py
source_files:
  - src/data_manager/collectors/persistence.py
  - src/data_manager/collectors/utils/index_utils.py
---

# Persistence Service Spec

## Overview

Shared filesystem persistence layer for collected resources. Manages file storage, metadata, and index tracking via CatalogService.

## Dependencies

- `src/data_manager/collectors/utils/index_utils.CatalogService`
- `src/data_manager/collectors/utils/metadata.ResourceMetadata`
- `src/data_manager/collectors/resource_base.BaseResource`

## Public API

### Classes

#### `PersistenceService`
```python
class PersistenceService:
    """Shared filesystem persistence for collected resources."""
    
    data_path: Path
    catalog: CatalogService
    _index_dirty: bool = False
    _metadata_index_dirty: bool = False
```

**Constructor:**
```python
def __init__(self, data_path: Path | str) -> None
```

**Contracts:**
- ENSURES: `data_path` converted to `Path`
- ENSURES: `CatalogService` initialized with data_path

**Methods:**

##### `persist_resource`
```python
def persist_resource(self, resource: BaseResource, target_dir: Path) -> Path
```
Write resource and metadata to disk.

**Contracts:**
- ENSURES: Creates `target_dir` if not exists
- ENSURES: Writes content via `_write_content`
- ENSURES: Writes metadata via `_write_metadata` if present
- ENSURES: Updates `catalog.file_index[hash] = relative_path`
- ENSURES: Updates `catalog.metadata_index[hash] = metadata_path`
- ENSURES: Returns file path

##### `delete_resource`
```python
def delete_resource(self, resource_hash: str, flush: bool = True) -> Path
```
Delete resource and metadata from disk.

**Contracts:**
- REQUIRES: `resource_hash` exists in both indices
- ENSURES: Removes files from filesystem
- ENSURES: Removes entries from indices
- ENSURES: Optionally flushes index

##### `flush_index`
```python
def flush_index(self) -> None
```
Persist index changes to disk.

**Contracts:**
- ENSURES: Writes file_index if dirty
- ENSURES: Writes metadata_index if dirty
- ENSURES: Resets dirty flags

##### `reset_directory`
```python
def reset_directory(self, directory: Path) -> None
```
Clear a directory and its index entries.

---

#### `CatalogService`
```python
class CatalogService:
    """Manages file and metadata indices."""
    
    data_path: Path
    file_index: Dict[str, str]      # hash -> relative_path
    metadata_index: Dict[str, str]  # hash -> metadata_path
```

**Contracts:**
- ENSURES: Loads existing indices from disk on init
- ENSURES: Creates indices directory if not exists

## Index Structure

```
{data_path}/
├── .index/
│   ├── file_index.yaml      # {hash: relative_path}
│   └── metadata_index.yaml  # {hash: metadata_path}
├── websites/
│   ├── doc1.html
│   └── doc1.html.meta.yaml
└── tickets/
    └── ...
```

## Invariants

1. Every resource has a unique hash
2. Metadata files use `.meta.yaml` suffix
3. Indices are only flushed when dirty
4. Relative paths are POSIX-style
