from typing import Optional
from app.config import settings
from .base import BaseLLMClient

# Singletons
_local_client = None
_gemini_client = None

def get_llm_client(provider_override: Optional[str] = None, **kwargs) -> BaseLLMClient:
    global _local_client, _gemini_client
    
    provider = provider_override or settings.DEFAULT_LLM_PROVIDER
    base_url = kwargs.get("custom_base_url")
    api_key = kwargs.get("custom_api_key")
    model = kwargs.get("custom_model")
    
    # Check if native Gemini is requested
    is_gemini = provider == "gemini" or (provider == "cloud" and not base_url and model and "gemini" in model.lower())
    
    if is_gemini:
        from .gemini import GeminiClient
        return GeminiClient(api_key=api_key, model=model)
    else:
        from .local_openai import LocalOpenAIClient
        return LocalOpenAIClient(
            base_url=base_url,
            api_key=api_key,
            model=model
        )
