"""
==========================================================
CareerFarm AI
LLM Loader
----------------------------------------------------------
Loads Gemini only once using Google SDK.
==========================================================
"""

import google.generativeai as genai

from ai.config import (
    APIConfig,
    ModelConfig,
)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_model = None


def get_llm():
    """
    Returns Gemini model singleton.
    """

    global _model

    if _model is not None:
        return _model

    logger.info("Loading Gemini...")

    genai.configure(api_key=APIConfig.GOOGLE_API_KEY)

    _model = genai.GenerativeModel(
        ModelConfig.MODEL_NAME
    )

    logger.info("Gemini Loaded Successfully.")

    return _model