"""Speech-to-text wiring.

`interview_service.answer` catches every exception from transcription and
reports "Could not transcribe your audio", so a *structurally* broken STT path
is indistinguishable from a bad recording. It shipped importing
`google.generativeai`, which is not a declared dependency and not installed,
so every voice answer failed that way. These tests assert the shape of the
call instead of the model's output, which is what actually regressed.
"""

import base64
from unittest.mock import MagicMock, patch

import pytest

from app.ai.llm import transcription
from app.services.audio_service import transcribe_audio


@pytest.fixture(autouse=True)
def _clear_model_cache():
    transcription._model.cache_clear()
    yield
    transcription._model.cache_clear()


def test_transcription_only_imports_declared_dependencies():
    """The provider SDK must be one that is actually in uv.lock."""
    import importlib.metadata as md

    md.distribution("langchain-google-genai")  # raises if absent

    with pytest.raises(md.PackageNotFoundError):
        md.distribution("google-generativeai")


def test_audio_is_sent_as_a_base64_media_part_with_its_own_mime_type():
    fake = MagicMock()
    fake.invoke.return_value = MagicMock(content="  hello world  ")

    with patch.object(transcription, "_model", return_value=fake):
        out = transcription.transcribe(b"RIFFfake-wav-bytes", "audio/wav")

    assert out == "hello world"

    (messages,) = fake.invoke.call_args.args
    parts = messages[0].content
    text_part, media_part = parts

    assert text_part["type"] == "text"
    assert media_part["type"] == "media"
    # The caller's type, not the default -- a wav labelled webm decodes to
    # silence rather than erroring.
    assert media_part["mime_type"] == "audio/wav"
    assert base64.b64decode(media_part["data"]) == b"RIFFfake-wav-bytes"


def test_multimodal_list_content_is_flattened():
    fake = MagicMock()
    fake.invoke.return_value = MagicMock(
        content=[{"type": "text", "text": "part one "}, {"type": "text", "text": "part two"}]
    )

    with patch.object(transcription, "_model", return_value=fake):
        assert transcription.transcribe(b"x", "audio/webm") == "part one part two"


def test_service_passes_the_mime_type_through():
    with patch.object(transcription, "transcribe") as inner:
        inner.return_value = "ok"
        # audio_service re-exports the same function object, so patch where it
        # is looked up.
        with patch("app.services.audio_service.transcribe", inner):
            assert transcribe_audio(b"bytes", "audio/mpeg") == "ok"
    inner.assert_called_once_with(b"bytes", "audio/mpeg")
