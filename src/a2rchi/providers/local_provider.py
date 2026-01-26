"""Local provider implementation for Ollama and OpenAI-compatible local servers."""

from typing import Any, Dict, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel

from src.a2rchi.providers.base import (
    BaseProvider,
    ModelInfo,
    ProviderConfig,
    ProviderType,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


# Common local models - these are just suggestions, actual models depend on what's installed
DEFAULT_LOCAL_MODELS = [
    ModelInfo(
        id="llama3.2",
        name="llama3.2",
        display_name="Llama 3.2 (Local)",
        context_window=128000,
        supports_tools=True,
        supports_streaming=True,
        supports_vision=True,
        max_output_tokens=8192,
    ),
    ModelInfo(
        id="llama3.1:8b",
        name="llama3.1:8b",
        display_name="Llama 3.1 8B (Local)",
        context_window=128000,
        supports_tools=True,
        supports_streaming=True,
        supports_vision=False,
        max_output_tokens=8192,
    ),
    ModelInfo(
        id="llama3.1:70b",
        name="llama3.1:70b",
        display_name="Llama 3.1 70B (Local)",
        context_window=128000,
        supports_tools=True,
        supports_streaming=True,
        supports_vision=False,
        max_output_tokens=8192,
    ),
    ModelInfo(
        id="qwen2.5:7b",
        name="qwen2.5:7b",
        display_name="Qwen 2.5 7B (Local)",
        context_window=32768,
        supports_tools=True,
        supports_streaming=True,
        supports_vision=False,
        max_output_tokens=8192,
    ),
    ModelInfo(
        id="mistral",
        name="mistral",
        display_name="Mistral (Local)",
        context_window=32768,
        supports_tools=True,
        supports_streaming=True,
        supports_vision=False,
        max_output_tokens=8192,
    ),
    ModelInfo(
        id="deepseek-r1:8b",
        name="deepseek-r1:8b",
        display_name="DeepSeek R1 8B (Local)",
        context_window=64000,
        supports_tools=False,
        supports_streaming=True,
        supports_vision=False,
        max_output_tokens=8192,
    ),
    ModelInfo(
        id="phi3",
        name="phi3",
        display_name="Phi-3 (Local)",
        context_window=4096,
        supports_tools=False,
        supports_streaming=True,
        supports_vision=False,
        max_output_tokens=4096,
    ),
]


class LocalProvider(BaseProvider):
    """
    Provider for local LLM servers (Ollama, vLLM, LM Studio, etc.)
    
    Supports two modes:
    1. Ollama mode (default): Uses ChatOllama from langchain_ollama
    2. OpenAI-compatible mode: Uses ChatOpenAI for vLLM, LM Studio, etc.
    
    The mode is determined by the 'local_mode' setting in extra_kwargs.
    """
    
    provider_type = ProviderType.LOCAL
    display_name = "Local Server"
    
    DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
    DEFAULT_OPENAI_COMPAT_BASE_URL = "http://localhost:8000/v1"
    
    def __init__(self, config: Optional[ProviderConfig] = None):
        if config is None:
            config = ProviderConfig(
                provider_type=ProviderType.LOCAL,
                base_url=self.DEFAULT_OLLAMA_BASE_URL,
                models=DEFAULT_LOCAL_MODELS,
                default_model="llama3.2",
                # Default to Ollama mode
                extra_kwargs={"local_mode": "ollama"},
            )
        super().__init__(config)
    
    @property
    def local_mode(self) -> str:
        """Get the local server mode (ollama or openai_compat)."""
        return self.config.extra_kwargs.get("local_mode", "ollama")
    
    def get_chat_model(self, model_name: str, **kwargs) -> BaseChatModel:
        """Get a local chat model instance."""
        mode = kwargs.pop("local_mode", self.local_mode)
        
        if mode == "openai_compat":
            return self._get_openai_compat_model(model_name, **kwargs)
        else:
            return self._get_ollama_model(model_name, **kwargs)
    
    def _get_ollama_model(self, model_name: str, **kwargs) -> BaseChatModel:
        """Get a ChatOllama instance."""
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError(
                "langchain_ollama is required for Ollama support. "
                "Install it with: pip install langchain-ollama"
            )
        
        model_kwargs = {
            "model": model_name,
            "streaming": True,
            **self.config.extra_kwargs,
            **kwargs,
        }
        
        # Remove local_mode from kwargs as ChatOllama doesn't accept it
        model_kwargs.pop("local_mode", None)
        
        if self.config.base_url:
            model_kwargs["base_url"] = self.config.base_url
            
        return ChatOllama(**model_kwargs)
    
    def _get_openai_compat_model(self, model_name: str, **kwargs) -> BaseChatModel:
        """Get a ChatOpenAI instance for OpenAI-compatible servers (vLLM, LM Studio)."""
        from langchain_openai import ChatOpenAI
        
        base_url = self.config.base_url or self.DEFAULT_OPENAI_COMPAT_BASE_URL
        
        model_kwargs = {
            "model": model_name,
            "base_url": base_url,
            "streaming": True,
            # Most local servers don't require an API key, but some do
            "api_key": self._api_key or "not-needed",
            **{k: v for k, v in self.config.extra_kwargs.items() if k != "local_mode"},
            **kwargs,
        }
        
        return ChatOpenAI(**model_kwargs)
    
    def list_models(self) -> List[ModelInfo]:
        """
        List available local models.
        
        For Ollama, this could potentially query the Ollama API to get installed models.
        For now, returns the configured models list.
        """
        if self.config.models:
            return self.config.models
        return DEFAULT_LOCAL_MODELS
    
    def validate_connection(self) -> bool:
        """
        Validate connection to the local server.
        
        For Ollama, checks if the server is running by hitting the /api/tags endpoint.
        For OpenAI-compatible, checks the /models endpoint.
        """
        import urllib.request
        import urllib.error
        
        try:
            if self.local_mode == "ollama":
                base_url = self.config.base_url or self.DEFAULT_OLLAMA_BASE_URL
                url = f"{base_url}/api/tags"
            else:
                base_url = self.config.base_url or self.DEFAULT_OPENAI_COMPAT_BASE_URL
                url = f"{base_url}/models"
            
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            logger.warning(f"Local server connection failed: {e}")
            return False
    
    def list_installed_models(self) -> List[str]:
        """
        Query Ollama for installed models (Ollama mode only).
        
        Returns a list of model names that are currently installed locally.
        """
        if self.local_mode != "ollama":
            logger.warning("list_installed_models is only available in Ollama mode")
            return []
        
        import json
        import urllib.request
        import urllib.error
        
        try:
            base_url = self.config.base_url or self.DEFAULT_OLLAMA_BASE_URL
            url = f"{base_url}/api/tags"
            
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    return [model["name"] for model in data.get("models", [])]
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to list installed Ollama models: {e}")
        
        return []
