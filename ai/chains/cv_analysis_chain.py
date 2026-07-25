"""Chain for the CV Analysis feature.

Pure orchestration: prompt -> structured-output LLM. No business logic,
no parsing, no data loading — that belongs in `ai.loaders` and the
schema itself.
"""

from langchain_core.runnables import Runnable

from ai.llm.gemini import get_gemini_model
from ai.prompts.cv_analysis_prompt import CV_ANALYSIS_PROMPT
from ai.schemas.cv_profile import CVProfile


def build_cv_analysis_chain() -> Runnable:
    """Build and return the CV Analysis Runnable chain."""
    structured_llm = get_gemini_model().with_structured_output(CVProfile)
    return CV_ANALYSIS_PROMPT | structured_llm