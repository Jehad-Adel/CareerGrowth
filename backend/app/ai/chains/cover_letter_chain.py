"""Chain for the Cover Letter feature.

Pure orchestration: default the optional title, then prompt -> structured
-output LLM. No business logic, no parsing.
"""

from langchain_core.runnables import Runnable, RunnableLambda

from app.ai.llm.gemini import get_gemini_model
from app.ai.prompts.cover_letter_prompt import COVER_LETTER_PROMPT
from app.ai.schemas.cover_letter_schema import CoverLetter

_NO_TITLE_PLACEHOLDER = "Not stated — infer it from the job description."


def _prepare_prompt_input(chain_input: dict) -> dict:
    """Default a missing job title to the prompt's placeholder."""
    return {
        "cv_text": chain_input["cv_text"],
        "job_description": chain_input["job_description"],
        "job_title": chain_input.get("job_title") or _NO_TITLE_PLACEHOLDER,
    }


def build_cover_letter_chain() -> Runnable:
    """Build and return the Cover Letter Runnable chain.

    Expects invoke() input as a dict with keys: cv_text (str),
    job_description (str), job_title (str | None, optional).
    """
    structured_llm = get_gemini_model().with_structured_output(CoverLetter)
    return RunnableLambda(_prepare_prompt_input) | COVER_LETTER_PROMPT | structured_llm
