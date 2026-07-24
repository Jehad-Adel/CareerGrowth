"""
==========================================================
CareerFarm AI
Configuration
----------------------------------------------------------
Centralized configuration for the entire AI module.
==========================================================
"""

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


# ==========================================================
# API Configuration
# ==========================================================

@dataclass(frozen=True)
class APIConfig:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# ==========================================================
# LLM Configuration
# ==========================================================

@dataclass(frozen=True)
class ModelConfig:
    MODEL_NAME = "gemini-flash-latest"


# ==========================================================
# Generation Configuration
# ==========================================================

@dataclass(frozen=True)
class GenerationConfig:
    TEMPERATURE = 0.2
    MAX_OUTPUT_TOKENS = 1024


# ==========================================================
# Application Configuration
# ==========================================================

@dataclass(frozen=True)
class AppConfig:
    DEBUG = True