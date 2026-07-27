"""Chain for the Career Chat feature.

Returns plain text rather than a structured object: a conversational reply has
no schema worth enforcing, and StrOutputParser keeps the surface small.
"""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable

from app.ai.llm.gemini import get_gemini_model
from app.ai.prompts.chat_prompt import CHAT_PROMPT


def build_chat_chain() -> Runnable:
    """Build the Career Chat Runnable.

    Expects invoke() input with keys: profile, context, history, question --
    all strings, all already delimited by the caller.
    """
    return CHAT_PROMPT | get_gemini_model() | StrOutputParser()
