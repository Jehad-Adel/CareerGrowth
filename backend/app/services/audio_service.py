"""Speech-to-text service.

Uses Gemini's built-in audio understanding rather than a separate STT API,
eliminating the need for an additional API key and reducing latency.

The provider call itself lives in `app.ai.llm.transcription` -- services do
not import model SDKs directly.
"""

from app.ai.llm.transcription import transcribe
from app.logging import get_logger

log = get_logger(__name__)


def transcribe_audio(audio_data: bytes, mime_type: str = "audio/webm") -> str:
    """Transcribe audio using Gemini's multimodal understanding.

    Args:
        audio_data: Raw audio bytes.
        mime_type: MIME type of the audio (e.g. audio/webm, audio/wav, audio/mp3).

    Returns:
        Transcribed text, or "" when the recording held nothing intelligible.
    """
    return transcribe(audio_data, mime_type)
