import os

from langchain_openai import ChatOpenAI


class OpenAILLM(ChatOpenAI):
    """
    Loading the various OpenAI models, most commonly

        model_name = 'gpt-4'
        model_name = 'gpt-3.5-turbo'

    Make sure that the api key is loaded as an environment variable
    and the OpenAI package installed.
    """

    model_name: str = "gpt-4"
    temperature: int = 1


class OpenRouterLLM(ChatOpenAI):
    """
    ChatOpenAI-compatible wrapper for OpenRouter.

    Configure using OPENROUTER_API_KEY and optional OPENROUTER_SITE_URL / OPENROUTER_APP_NAME
    for OpenRouter attribution headers.
    """

    model_name: str = "openai/gpt-4o-mini"
    temperature: float = 1.0
    base_url: str = "https://openrouter.ai/api/v1"

    def __init__(self, **kwargs):
        if "api_key" not in kwargs:
            env_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
            if env_key:
                kwargs["api_key"] = env_key

        kwargs.setdefault("base_url", "https://openrouter.ai/api/v1")
        kwargs.setdefault("streaming", True)

        if "default_headers" not in kwargs:
            headers = {}
            site_url = os.getenv("OPENROUTER_SITE_URL")
            app_name = os.getenv("OPENROUTER_APP_NAME")
            if site_url:
                headers["HTTP-Referer"] = site_url
            if app_name:
                headers["X-Title"] = app_name
            if headers:
                kwargs["default_headers"] = headers

        super().__init__(**kwargs)
