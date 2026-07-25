"""Chain for the Interview Simulator feature.

Pure orchestration: format conversation state -> prompt -> structured
-output LLM. No business logic or manual output parsing.
"""

from langchain_core.runnables import Runnable, RunnableLambda

from ai.llm.gemini import get_gemini_model
from ai.prompts.interview_prompt import INTERVIEW_PROMPT
from ai.schemas.interview_schema import ConversationTurn, InterviewLevel, InterviewResponse

_NO_INTERVIEWER_NAME_PLACEHOLDER = "Not yet assigned"


def _format_conversation_history(history: list[ConversationTurn]) -> str:
    """Render conversation turns as readable Q/A text for the prompt."""
    if not history:
        return "No prior conversation. This is the first question of the interview."

    return "\n\n".join(
        f"Q{i}: {turn.question}\nA{i}: {turn.answer}"
        for i, turn in enumerate(history, start=1)
    )


def _prepare_prompt_input(chain_input: dict) -> dict:
    """Convert the chain's structured input into the prompt's string variables."""
    return {
        "cv_text": chain_input["cv_text"],
        "job_description": chain_input["job_description"],
        "interview_level": InterviewLevel(chain_input["interview_level"]).value,
        "conversation_history": _format_conversation_history(
            chain_input["conversation_history"]
        ),
        "interviewer_name": chain_input.get("interviewer_name")
        or _NO_INTERVIEWER_NAME_PLACEHOLDER,
    }


def build_interview_chain() -> Runnable:
    """Build and return the Interview Simulator Runnable chain.

    Expects invoke() input as a dict with keys: cv_text (str),
    job_description (str), interview_level (InterviewLevel | str),
    conversation_history (list[ConversationTurn]), interviewer_name
    (str | None, optional — omit or pass None on the first question,
    then pass back the interviewer_name returned by the previous turn
    to keep the same interviewer for the rest of the conversation).
    """
    structured_llm = get_gemini_model().with_structured_output(InterviewResponse)
    return RunnableLambda(_prepare_prompt_input) | INTERVIEW_PROMPT | structured_llm