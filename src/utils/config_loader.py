import os

import yaml

# DEFINITIONS - allow override via environment variable
_configs_path = os.environ.get("A2RCHI_CONFIGS_PATH", os.environ.get("ARCHI_CONFIGS_PATH", "/root/archi/configs/"))
# Ensure trailing slash
CONFIGS_PATH = _configs_path if _configs_path.endswith("/") else _configs_path + "/"

def load_config(map: bool = False, name: str = None):
    """
    Load the configuration specified by name, or the first one by default.
    Optionally maps models to the corresponding class.
    """

    if name is None:
        default_path = CONFIGS_PATH + os.listdir(CONFIGS_PATH)[0]
        with open(default_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    else:
        with open(CONFIGS_PATH+f"{name}.yaml", "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

    # change the model class parameter from a string to an actual class
    if map:

        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_openai import OpenAIEmbeddings

        from src.archi.models import (VLLM, AnthropicLLM, DumbLLM,
                           HuggingFaceImageLLM, HuggingFaceOpenLLM,
                           LlamaLLM, OllamaInterface, OpenAILLM,
                           OpenRouterLLM)
        from src.data_manager.collectors.scrapers.integrations.sso_scraper import \
            CERNSSOScraper
        
        MODEL_MAPPING = {
            "AnthropicLLM": AnthropicLLM,
            "OpenAILLM": OpenAILLM,
            "OpenRouterLLM": OpenRouterLLM,
            "DumbLLM": DumbLLM,
            "LlamaLLM": LlamaLLM,
            "HuggingFaceOpenLLM": HuggingFaceOpenLLM,
            "HuggingFaceImageLLM": HuggingFaceImageLLM,
            "VLLM": VLLM,
            "OllamaInterface": OllamaInterface, 
        }
        for model in config["archi"]["model_class_map"].keys():
            config["archi"]["model_class_map"][model]["class"] = MODEL_MAPPING[model]

        EMBEDDING_MAPPING = {
            "OpenAIEmbeddings": OpenAIEmbeddings,
            "HuggingFaceEmbeddings": HuggingFaceEmbeddings
        }
        for model in config["data_manager"]["embedding_class_map"].keys():
            config["data_manager"]["embedding_class_map"][model]["class"] = EMBEDDING_MAPPING[model]

        # change the SSO class parameter from a string to an actual class
        sources_links = config.get('data_manager', {}).get('sources', {}).get('links', {}) or {}
        selenium_scraper = sources_links.get('selenium_scraper', {}) or {}

        if selenium_scraper:
            SSO_MAPPING = {
                'CERNSSOScraper': CERNSSOScraper,
            }
            selenium_class_map = selenium_scraper.get('selenium_class_map', {})
            for sso_class in selenium_class_map.keys():
                if sso_class in SSO_MAPPING:
                    selenium_class_map[sso_class]['class'] = SSO_MAPPING[sso_class]

    return config

def load_global_config(name: str = None):
    """
    Load the global part of the config.yaml file.
    This is assumed to be static.
    """

    if name is None:
        default_path = CONFIGS_PATH + os.listdir(CONFIGS_PATH)[0]
        with open(default_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    else:
        with open(CONFIGS_PATH+f"{name}.yaml", "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

    return config["global"]

def load_data_manager_config(name: str = None):
    """
    Load the data_manager part of the config.yaml file.
    This is assumed to be static.
    """

    if name is None:
        default_path = CONFIGS_PATH + os.listdir(CONFIGS_PATH)[0]
        with open(default_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    else:
        with open(CONFIGS_PATH+f"{name}.yaml", "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

    return config["data_manager"]

def load_services_config(name: str = None):
    """
    Load the services part of the config.yaml file.
    This is assumed to be static.
    """

    if name is None:
        default_path = CONFIGS_PATH + os.listdir(CONFIGS_PATH)[0]
        with open(default_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    else:
        with open(CONFIGS_PATH+f"{name}.yaml", "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

    return config["services"]

def get_config_names():
    """
    Gets the available configurations names.
    """

    names = [n.replace('.yaml','') for n in os.listdir(CONFIGS_PATH)]
    return names
