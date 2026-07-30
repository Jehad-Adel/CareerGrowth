from langchain_core.runnables import Runnable

from app.ai.llm.gemini import get_gemini_model
from app.ai.prompts.quiz_prompt import QUIZ_GENERATE_PROMPT
from app.ai.schemas.quiz_schema import QuizResponse


def build_quiz_chain() -> Runnable:
    structured_llm = get_gemini_model().with_structured_output(QuizResponse)
    return QUIZ_GENERATE_PROMPT | structured_llm
