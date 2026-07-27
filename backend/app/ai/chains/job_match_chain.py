"""Chain for the Job Match feature.

Pure orchestration: prompt -> structured-output LLM. No business logic,
no parsing — that belongs in the schema and loaders.
"""

from langchain_core.runnables import Runnable

from app.ai.llm.gemini import get_gemini_model
from app.ai.prompts.job_match_prompt import JOB_MATCH_PROMPT
from app.ai.schemas.job_match_schema import JobMatch


def build_job_match_chain() -> Runnable:
    """Build and return the Job Match Runnable chain."""
    structured_llm = get_gemini_model().with_structured_output(JobMatch)
    return JOB_MATCH_PROMPT | structured_llm