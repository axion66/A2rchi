"""
ModelRegistry - Centralized mapping of model names to classes.

Replaces the ad-hoc model class mapping in config_loader.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Type

if TYPE_CHECKING:
    from src.archi.models.base import BaseCustomLLM


class ModelRegistry:
    """
    Singleton registry mapping model names to their classes.
    
    Usage:
        >>> ModelRegistry.get("OpenAILLM")
        <class 'src.archi.models.openai.OpenAILLM'>
        
        >>> ModelRegistry.get("UnknownModel")  
        None
        
        >>> ModelRegistry.get_all_names()
        ['AnthropicLLM', 'OpenAILLM', 'OpenRouterLLM', ...]
    """
    
    _models: Dict[str, Type["BaseCustomLLM"]] = {}
    _initialized: bool = False
    
    @classmethod
    def _ensure_initialized(cls) -> None:
        """Lazily initialize the registry to avoid circular imports."""
        if cls._initialized:
            return
        
        # Import here to avoid circular imports at module load time
        from src.archi.models import (
            AnthropicLLM,
            ClaudeLLM,
            DumbLLM,
            HuggingFaceImageLLM,
            HuggingFaceOpenLLM,
            LlamaLLM,
            OllamaInterface,
            OpenAILLM,
            OpenRouterLLM,
            VLLM,
        )
        
        cls._models = {
            "AnthropicLLM": AnthropicLLM,
            "ClaudeLLM": ClaudeLLM,
            "DumbLLM": DumbLLM,
            "HuggingFaceImageLLM": HuggingFaceImageLLM,
            "HuggingFaceOpenLLM": HuggingFaceOpenLLM,
            "LlamaLLM": LlamaLLM,
            "OllamaInterface": OllamaInterface,
            "OpenAILLM": OpenAILLM,
            "OpenAIGPT4": OpenAILLM,      # Alias for backward compat
            "OpenAIGPT35": OpenAILLM,     # Alias for backward compat
            "OpenRouterLLM": OpenRouterLLM,
            "VLLM": VLLM,
        }
        cls._initialized = True
    
    @classmethod
    def get(cls, name: str) -> Optional[Type["BaseCustomLLM"]]:
        """
        Get a model class by name.
        
        Args:
            name: The model class name (e.g., "OpenAILLM", "AnthropicLLM")
            
        Returns:
            The model class, or None if not found
        """
        cls._ensure_initialized()
        return cls._models.get(name)
    
    @classmethod
    def get_or_raise(cls, name: str) -> Type["BaseCustomLLM"]:
        """
        Get a model class by name, raising if not found.
        
        Args:
            name: The model class name
            
        Returns:
            The model class
            
        Raises:
            KeyError: If the model name is not registered
        """
        cls._ensure_initialized()
        if name not in cls._models:
            available = ", ".join(cls._models.keys())
            raise KeyError(f"Unknown model: {name}. Available: {available}")
        return cls._models[name]
    
    @classmethod
    def get_all_names(cls) -> list[str]:
        """Get all registered model names."""
        cls._ensure_initialized()
        return list(cls._models.keys())
    
    @classmethod
    def register(cls, name: str, model_class: Type["BaseCustomLLM"]) -> None:
        """
        Register a new model class.
        
        Useful for plugins or testing.
        
        Args:
            name: The name to register under
            model_class: The model class to register
        """
        cls._ensure_initialized()
        cls._models[name] = model_class


class EmbeddingRegistry:
    """
    Singleton registry mapping embedding names to their classes.
    
    Usage:
        >>> EmbeddingRegistry.get("OpenAIEmbeddings")
        <class 'langchain_openai.embeddings.OpenAIEmbeddings'>
    """
    
    _embeddings: Dict[str, Type] = {}
    _initialized: bool = False
    
    @classmethod
    def _ensure_initialized(cls) -> None:
        """Lazily initialize the registry."""
        if cls._initialized:
            return
        
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_openai import OpenAIEmbeddings
        
        cls._embeddings = {
            "OpenAIEmbeddings": OpenAIEmbeddings,
            "HuggingFaceEmbeddings": HuggingFaceEmbeddings,
        }
        cls._initialized = True
    
    @classmethod
    def get(cls, name: str) -> Optional[Type]:
        """Get an embedding class by name."""
        cls._ensure_initialized()
        return cls._embeddings.get(name)
    
    @classmethod
    def get_or_raise(cls, name: str) -> Type:
        """Get an embedding class by name, raising if not found."""
        cls._ensure_initialized()
        if name not in cls._embeddings:
            available = ", ".join(cls._embeddings.keys())
            raise KeyError(f"Unknown embedding: {name}. Available: {available}")
        return cls._embeddings[name]
    
    @classmethod
    def get_all_names(cls) -> list[str]:
        """Get all registered embedding names."""
        cls._ensure_initialized()
        return list(cls._embeddings.keys())
    
    @classmethod
    def register(cls, name: str, embedding_class: Type) -> None:
        """Register a new embedding class."""
        cls._ensure_initialized()
        cls._embeddings[name] = embedding_class
