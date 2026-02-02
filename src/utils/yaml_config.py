"""
YAML configuration loader with Postgres-backed runtime source of truth.

Runtime behavior:
- Reads configuration from PostgreSQL (raw_config table) via ConfigService / PostgresServiceFactory.
- Does not fall back to filesystem YAML at runtime. Bootstrap code must ingest YAML into Postgres first.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.utils.postgres_service_factory import PostgresServiceFactory


# Default config path - can be overridden with ARCHI_CONFIGS_PATH env var
CONFIGS_PATH = os.environ.get("ARCHI_CONFIGS_PATH", "/root/archi/configs/")


def _get_config_from_db() -> Optional[Dict[str, Any]]:
    """Deprecated helper; returns None (raw_config removed)."""
    return None


def _get_configs_path() -> str:
    """Get the configs path, with environment override support."""
    return os.environ.get("ARCHI_CONFIGS_PATH", CONFIGS_PATH)


def list_config_names() -> List[str]:
    """
    Get available configuration names (without .yaml extension).
    
    Returns:
        List of config names found in CONFIGS_PATH.
    """
    raise RuntimeError("list_config_names is removed. Query config via ConfigService.")


def load_yaml_config(name: Optional[str] = None) -> Dict[str, Any]:
    """
    Deprecated. Use src.utils.config_access.get_raw_config().
    Kept only to surface a clear error if legacy imports remain.
    """
    raise RuntimeError("load_yaml_config is removed. Use ConfigService via PostgresServiceFactory (see config_access.get_raw_config()).")


def load_global_config(name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the 'global' section of the config.
    
    Args:
        name: Config name (without .yaml extension).
        
    Returns:
        Dictionary containing global configuration.
    """
    from src.utils.config_access import get_global_config
    return get_global_config()


def load_services_config(name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the 'services' section of the config.
    
    Args:
        name: Config name (without .yaml extension).
        
    Returns:
        Dictionary containing services configuration.
    """
    from src.utils.config_access import get_services_config
    return get_services_config()


def load_data_manager_config(name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the 'data_manager' section of the config.
    
    Args:
        name: Config name (without .yaml extension).
        
    Returns:
        Dictionary containing data_manager configuration.
    """
    from src.utils.config_access import get_data_manager_config
    return get_data_manager_config()


def load_archi_config(name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the 'archi' section of the config.
    
    Args:
        name: Config name (without .yaml extension).
        
    Returns:
        Dictionary containing archi configuration.
    """
    from src.utils.config_access import get_archi_config
    return get_archi_config()


def get_model_class_map(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Get model class mapping from config and resolve to actual classes.
    
    Uses ModelRegistry for class resolution.
    
    Args:
        config: Full configuration dictionary.
        
    Returns:
        Model class map with 'class' values resolved to actual Python classes.
    """
    from src.archi.models.registry import ModelRegistry
    
    model_class_map = config.get("archi", {}).get("model_class_map", {})
    result = {}
    
    for model_name, model_config in model_class_map.items():
        result[model_name] = model_config.copy()
        # Resolve class name to actual class using registry
        model_class = ModelRegistry.get(model_name)
        if model_class:
            result[model_name]["class"] = model_class
            
    return result


def get_embedding_class_map(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Get embedding class mapping from config and resolve to actual classes.
    
    Uses EmbeddingRegistry for class resolution.
    
    Args:
        config: Full configuration dictionary.
        
    Returns:
        Embedding class map with 'class' values resolved to actual Python classes.
    """
    from src.archi.models.registry import EmbeddingRegistry
    
    embedding_class_map = config.get("data_manager", {}).get("embedding_class_map", {})
    result = {}
    
    for embedding_name, embedding_config in embedding_class_map.items():
        result[embedding_name] = embedding_config.copy()
        # Resolve class name to actual class using registry
        embedding_class = EmbeddingRegistry.get(embedding_name)
        if embedding_class:
            result[embedding_name]["class"] = embedding_class
            
    return result


def load_config_with_class_mapping(name: Optional[str] = None, *, factory=None) -> Dict[str, Any]:
    """
    Resolve model/embedding class names to actual classes from Postgres raw_config.
    """
    from src.utils.config_access import get_full_config

    _ = name  # unused; present for compatibility
    _ = factory

    config = get_full_config()

    if "archi" in config and "model_class_map" in config["archi"]:
        config["archi"]["model_class_map"] = get_model_class_map(config)

    if "data_manager" in config and "embedding_class_map" in config["data_manager"]:
        config["data_manager"]["embedding_class_map"] = get_embedding_class_map(config)

    return config
