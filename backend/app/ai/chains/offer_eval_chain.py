from langchain_core.runnables import Runnable

from app.ai.llm.gemini import get_gemini_model
from app.ai.prompts.offer_eval_prompt import OFFER_EVAL_PROMPT
from app.ai.schemas.offer_eval_schema import OfferEvaluationResult


def build_offer_eval_chain() -> Runnable:
    structured_llm = get_gemini_model().with_structured_output(OfferEvaluationResult)
    return OFFER_EVAL_PROMPT | structured_llm
