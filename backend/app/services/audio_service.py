"""Speech-to-text service using Google Gemini's multimodal capabilities.

Uses Gemini's built-in audio understanding rather than a separate STT API,
eliminating the need for an additional API key and reducing latency.
"""

import base64
import io

from app.ai.llm.gemini import get_gemini_model
from app.logging import get_logger

log = get_logger(__name__)


def transcribe_audio(audio_data: bytes, mime_type: str = "audio/webm") -> str:
    """Transcribe audio using Gemini's multimodal understanding.

    Args:
        audio_data: Raw audio bytes.
        mime_type: MIME type of the audio (e.g. audio/webm, audio/wav, audio/mp3).

    Returns:
        Transcribed text as a string.
    """
    import google.generativeai as genai
    from app.config import get_settings

    settings = get_settings()
    genai.configure(api_key=settings.google_api_key)

    model = genai.GenerativeModel(settings.gemini_model)

    prompt = (
        "Transcribe the spoken audio in this recording accurately. "
        "Output only the transcription, nothing else. "
        "If the audio is unclear or silent, output an empty string."
    )

    audio_part = {
        "mime_type": mime_type,
        "data": base64.b64encode(audio_data).decode("utf-8"),
    }

    response = model.generate_content([prompt, audio_part])

    return response.text.strip() if response.text else ""
