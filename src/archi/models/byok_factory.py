"""
BYOK-aware Model Factory.

Provides factory methods for creating LLM instances that support
per-user API keys (Bring Your Own Key). This allows users to use
their own API keys stored encrypted in PostgreSQL.

The factory checks for user-specific BYOK keys first, falling back
to environment-configured keys if no user key is available.
"""

from typing import Any, Dict, Optional, Type

from langchain_core.language_models.chat_models import BaseChatModel

from src.archi.providers import get_provider
from src.archi.providers.base import ProviderConfig, ProviderType
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Thread-local storage for current user context
import threading
_user_context = threading.local()


def set_current_user(user_id: Optional[str], user_service=None):
    """
    Set the current user context for BYOK resolution.
    
    Call this at the beginning of a request to enable BYOK for all
    subsequent model creations in this thread.
    
    Args:
        user_id: The user's identifier
        user_service: Optional UserService instance for key lookup
    """
    _user_context.user_id = user_id
    _user_context.user_service = user_service


def clear_current_user():
    """Clear the current user context."""
    _user_context.user_id = None
    _user_context.user_service = None


def get_current_user_id() -> Optional[str]:
    """Get the current user ID if set."""
    return getattr(_user_context, 'user_id', None)


def _get_user_service():
    """Get the user service from context."""
    return getattr(_user_context, 'user_service', None)


def _lookup_byok_key(provider_type: ProviderType) -> Optional[str]:
    """
    Look up BYOK API key for current user.
    
    Returns:
        Decrypted API key if available, None otherwise
    """
    user_id = get_current_user_id()
    if not user_id:
        return None
    
    user_service = _get_user_service()
    if not user_service:
        return None
    
    # Map provider type to BYOK provider name
    byok_map = {
        ProviderType.OPENAI: "openai",
        ProviderType.ANTHROPIC: "anthropic",
        ProviderType.OPENROUTER: "openrouter",
    }
    
    byok_provider = byok_map.get(provider_type)
    if not byok_provider:
        return None
    
    try:
        key = user_service.get_api_key(user_id, byok_provider)
        if key:
            logger.info(f"Using BYOK key for user {user_id}, provider {byok_provider}")
        return key
    except Exception as e:
        logger.warning(f"Failed to lookup BYOK key: {e}")
        return None


def create_model_with_byok(
    model_class: Type[BaseChatModel],
    model_kwargs: Dict[str, Any],
    provider_type: Optional[str] = None,
) -> BaseChatModel:
    """
    Create a model instance, using BYOK key if available.
    
    This is a drop-in replacement for direct model instantiation that
    adds BYOK support transparently.
    
    Args:
        model_class: The LangChain model class to instantiate
        model_kwargs: Keyword arguments for the model constructor
        provider_type: Provider type hint (e.g., "openai", "anthropic")
        
    Returns:
        Configured model instance
    """
    # Try to detect provider type from class name if not provided
    if provider_type is None:
        class_name = model_class.__name__.lower()
        if 'openai' in class_name or 'chatgpt' in class_name:
            provider_type = "openai"
        elif 'anthropic' in class_name or 'claude' in class_name:
            provider_type = "anthropic"
        elif 'gemini' in class_name or 'google' in class_name:
            provider_type = "gemini"
    
    # Look up BYOK key if we have a provider type
    byok_key = None
    if provider_type:
        try:
            pt = ProviderType(provider_type.lower())
            byok_key = _lookup_byok_key(pt)
        except ValueError:
            pass
    
    # Merge BYOK key into kwargs if found
    final_kwargs = dict(model_kwargs)
    if byok_key:
        # Different model classes use different parameter names
        # ChatOpenAI uses api_key, ChatAnthropic uses anthropic_api_key, etc.
        if 'openai' in (provider_type or '').lower():
            final_kwargs['api_key'] = byok_key
        elif 'anthropic' in (provider_type or '').lower():
            final_kwargs['anthropic_api_key'] = byok_key
        elif 'google' in (provider_type or '').lower() or 'gemini' in (provider_type or '').lower():
            final_kwargs['google_api_key'] = byok_key
    
    return model_class(**final_kwargs)


def get_chat_model_with_byok(
    provider_type: str,
    model_name: str,
    **kwargs,
) -> BaseChatModel:
    """
    Get a chat model using the provider system with BYOK support.
    
    This uses the provider abstraction layer which handles all the
    differences between providers automatically.
    
    Args:
        provider_type: Provider type ("openai", "anthropic", "gemini", etc.)
        model_name: Model name/ID
        **kwargs: Additional model kwargs
        
    Returns:
        Configured chat model
    """
    try:
        pt = ProviderType(provider_type.lower())
    except ValueError:
        raise ValueError(f"Unknown provider type: {provider_type}")
    
    # Check for BYOK key
    byok_key = _lookup_byok_key(pt)
    
    if byok_key:
        # Create provider with BYOK key (don't cache user-specific instances)
        config = ProviderConfig(
            provider_type=pt,
            api_key=byok_key,
        )
        provider = get_provider(provider_type, config=config, use_cache=False)
    else:
        # Use default provider (cached)
        provider = get_provider(provider_type, use_cache=True)
    
    return provider.get_chat_model(model_name, **kwargs)


class BYOKModelFactory:
    """
    Factory for creating LLM instances with BYOK support.
    
    Can be used as a replacement for direct model instantiation in
    pipeline configuration.
    
    Example:
        factory = BYOKModelFactory(user_service=user_service)
        
        # During request handling:
        factory.set_user("user_123")
        model = factory.create_model(ChatOpenAI, model="gpt-4o")
        
        # After request:
        factory.clear_user()
    """
    
    def __init__(self, user_service=None, pg_config: Optional[Dict[str, Any]] = None):
        """
        Initialize factory.
        
        Args:
            user_service: UserService instance for key lookup
            pg_config: PostgreSQL config (creates UserService if needed)
        """
        self._user_service = user_service
        self._pg_config = pg_config
        self._user_id: Optional[str] = None
    
    def _get_user_service(self):
        """Lazily initialize UserService."""
        if self._user_service is None and self._pg_config:
            from src.utils.user_service import UserService
            self._user_service = UserService(self._pg_config)
        return self._user_service
    
    def set_user(self, user_id: Optional[str]):
        """Set the current user for BYOK resolution."""
        self._user_id = user_id
        set_current_user(user_id, self._get_user_service())
    
    def clear_user(self):
        """Clear the current user context."""
        self._user_id = None
        clear_current_user()
    
    def create_model(
        self,
        model_class: Type[BaseChatModel],
        provider_type: Optional[str] = None,
        **kwargs,
    ) -> BaseChatModel:
        """
        Create a model instance with BYOK support.
        
        Args:
            model_class: LangChain model class
            provider_type: Provider type hint
            **kwargs: Model constructor arguments
            
        Returns:
            Model instance
        """
        return create_model_with_byok(model_class, kwargs, provider_type)
    
    def get_chat_model(
        self,
        provider_type: str,
        model_name: str,
        **kwargs,
    ) -> BaseChatModel:
        """
        Get a chat model using the provider system.
        
        Args:
            provider_type: Provider type
            model_name: Model name/ID
            **kwargs: Additional model kwargs
            
        Returns:
            Chat model instance
        """
        return get_chat_model_with_byok(provider_type, model_name, **kwargs)


# Convenience context manager for request handling
class byok_context:
    """
    Context manager for BYOK user context.
    
    Example:
        with byok_context(user_id="user_123", user_service=user_service):
            model = ChatOpenAI(...)  # Will use BYOK key if available
    """
    
    def __init__(self, user_id: Optional[str], user_service=None):
        self.user_id = user_id
        self.user_service = user_service
    
    def __enter__(self):
        set_current_user(self.user_id, self.user_service)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        clear_current_user()
        return False
