"""Chain for the Personalized Roadmap feature."""

from langchain_core.runnables import Runnable

from ai.llm.gemini import get_gemini_model
from ai.prompts.roadmap_prompt import ROADMAP_PROMPT
from ai.schemas.roadmap_schema import CareerRoadmap


def build_roadmap_chain() -> Runnable:
    """Build and return the Roadmap Runnable chain."""
    structured_llm = get_gemini_model().with_structured_output(CareerRoadmap)
    return ROADMAP_PROMPT | structured_llm