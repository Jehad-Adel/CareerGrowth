"""Chain for the AI Resume Optimizer feature.

Pure orchestration: default the optional job description, then
prompt -> structured-output LLM. No business logic, no parsing.
"""

from langchain_core.runnables import Runnable, RunnableLambda

from app.ai.llm.gemini import get_gemini_model
from app.ai.prompts.resume_optimizer_prompt import RESUME_OPTIMIZER_PROMPT
from app.ai.schemas.resume_optimizer_schema import ResumeOptimization

_NO_JOB_DESCRIPTION_PLACEHOLDER = "Not provided"


def _prepare_prompt_input(chain_input: dict) -> dict:
    """Default a missing or empty job_description to the prompt's placeholder."""
    job_description = chain_input.get("job_description") or _NO_JOB_DESCRIPTION_PLACEHOLDER
    return {
        "cv_text": chain_input["cv_text"],
        "job_description": job_description,
    }


def build_resume_optimizer_chain() -> Runnable:
    """Build and return the AI Resume Optimizer Runnable chain.

    Expects invoke() input as a dict with keys: cv_text (str),
    job_description (str | None, optional).
    """
    structured_llm = get_gemini_model().with_structured_output(ResumeOptimization)
    return RunnableLambda(_prepare_prompt_input) | RESUME_OPTIMIZER_PROMPT | structured_llm