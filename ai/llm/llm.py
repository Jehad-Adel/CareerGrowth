from langchain_google_genai import ChatGoogleGenerativeAI

from ai.config import (
    APIConfig,
    ModelConfig,
    GenerationConfig,
)

_llm = None


def get_llm():
    global _llm

    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model=ModelConfig.MODEL_NAME,
            google_api_key=APIConfig.GOOGLE_API_KEY,
            temperature=GenerationConfig.TEMPERATURE,
        )

    return _llm