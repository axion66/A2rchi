"""
Config access helpers that read from ConfigService / Postgres only.
No YAML fallback or raw_config usage.
"""

from typing import Any, Dict

from src.utils.postgres_service_factory import PostgresServiceFactory
from src.utils.config_service import ConfigService


class ConfigNotReadyError(RuntimeError):
    pass


def _config_service() -> ConfigService:
    factory = PostgresServiceFactory.get_instance()
    if not factory:
        raise ConfigNotReadyError("PostgresServiceFactory not initialized. Set it before accessing config.")
    return factory.config_service


def get_static_config():
    cfg = _config_service().get_static_config()
    if cfg is None:
        raise ConfigNotReadyError("Static config not initialized in Postgres.")
    return cfg


def get_dynamic_config():
    return _config_service().get_dynamic_config()


def get_global_config() -> Dict[str, Any]:
    return get_static_config().global_config or {}


def get_services_config() -> Dict[str, Any]:
    return get_static_config().services_config or {}


def get_data_manager_config() -> Dict[str, Any]:
    return get_static_config().data_manager_config or {}


def get_archi_config() -> Dict[str, Any]:
    return get_static_config().archi_config or {}


def get_full_config() -> Dict[str, Any]:
    static = get_static_config()
    return {
        "name": static.deployment_name,
        "config_version": static.config_version,
        "global": static.global_config,
        "services": static.services_config,
        "data_manager": static.data_manager_config,
        "archi": static.archi_config,
        "sources": static.sources_config,
        "available_pipelines": static.available_pipelines,
        "available_models": static.available_models,
        "available_providers": static.available_providers,
    }
