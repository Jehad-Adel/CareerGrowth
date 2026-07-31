"""Speech-to-text over Gemini's multimodal input.

Lives under `app/ai/` because it talks to the model provider directly, and
only `app/ai/` is allowed to. `audio_service` is the thin service wrapper
around it.

This deliberately goes through `langchain_google_genai`, the same dependency
every chain uses, rather than the standalone `google.generativeai` package.
That package is not declared in `pyproject.toml`, is not in `uv.lock`, and is
not installed -- importing it raised `ModuleNotFoundError` at the first audio
answer, which `interview_service` caught and reported as "could not
transcribe your audio", so the feature read as flaky rather than absent.
"""

import base64
from functools import lru_cache

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_settings

# Transcription is a copying task, not a generative one: any temperature above
# zero just invites the model to tidy up what it heard.
_TEMPERATURE = 0.0

# Long enough for a five-minute spoken answer. The route caps uploads at 5 MB,
# which is the real bound on how much audio can arrive.
_MAX_OUTPUT_TOKENS = 4096

_PROMPT = (
    "Transcribe the spoken audio in this recording verbatim. "
    "Output only the transcription, with no preamble, commentary, or "
    "formatting. If the audio is silent or unintelligible, output nothing."
)


@lru_cache
def _model() -> ChatGoogleGenerativeAI:
    """Cached, process-wide. Separate from `get_gemini_model` because the
    generation parameters differ -- that one carries the chains' temperature."""
    settings = get_settings()
    if not settings.google_api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and fill it in."
        )
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=_TEMPERATURE,
        max_output_tokens=_MAX_OUTPUT_TOKENS,
    )


def transcribe(audio_data: bytes, mime_type: str = "audio/webm") -> str:
    """Transcribe raw audio bytes. Returns "" when nothing was intelligible.

    `mime_type` must be the type the client actually sent. Gemini decodes the
    container from it, so labelling a wav as webm yields either an error or
    silence -- the caller has the real value from the upload header and should
    pass it rather than relying on the default.
    """
    message = HumanMessage(
        content=[
            {"type": "text", "text": _PROMPT},
            {
                "type": "media",
                "mime_type": mime_type,
                "data": base64.b64encode(audio_data).decode("ascii"),
            },
        ]
    )

    response = _model().invoke([message])

    # Multimodal replies can come back as a list of content blocks rather than
    # a plain string, so flatten before stripping.
    content = response.content
    if isinstance(content, list):
        content = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return content.strip()
