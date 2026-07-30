from langchain_core.runnables import Runnable

from app.ai.llm.gemini import get_gemini_model
from app.ai.prompts.video_summary_prompt import VIDEO_SUMMARY_PROMPT
from app.ai.schemas.video_schema import VideoSummaryResult


def build_video_summary_chain() -> Runnable:
    structured_llm = get_gemini_model().with_structured_output(VideoSummaryResult)
    return VIDEO_SUMMARY_PROMPT | structured_llm
