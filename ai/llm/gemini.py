"""Factory for the Google Gemini chat model.

Every chain gets its LLM instance from here instead of constructing
ChatGoogleGenerativeAI directly, so model selection and generation
parameters stay centralized in `ai.config`.
"""

from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from ai.config import get_settings


@lru_cache
def get_gemini_model() -> ChatGoogleGenerativeAI:
    """Return a cached, process-wide Gemini chat model instance."""
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=settings.temperature,
        max_output_tokens=settings.max_output_tokens,
    )