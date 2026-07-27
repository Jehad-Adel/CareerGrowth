"""Chain for the Skill Gap Analyzer feature.

Pure orchestration: prompt -> structured-output LLM. No business logic,
no parsing.
"""

from langchain_core.runnables import Runnable

from app.ai.llm.gemini import get_gemini_model
from app.ai.prompts.skill_gap_prompt import SKILL_GAP_PROMPT
from app.ai.schemas.skill_gap_schema import SkillGapAnalysis


def build_skill_gap_chain() -> Runnable:
    """Build and return the Skill Gap Analyzer Runnable chain."""
    structured_llm = get_gemini_model().with_structured_output(SkillGapAnalysis)
    return SKILL_GAP_PROMPT | structured_llm