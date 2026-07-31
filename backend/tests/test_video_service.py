"""Transcript fetching.

The video path shipped calling `YouTubeTranscriptApi.get_transcript`, a
classmethod removed in youtube-transcript-api 1.0, against a dependency that
was never in `pyproject.toml` at all -- so every summary failed with the
install hint rather than a transcript. These tests pin the 1.x call shape and
the error mapping, which is what actually regressed.
"""

from unittest.mock import MagicMock, patch

import pytest
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled

from app.services import video_service
from app.services.video_service import AnalysisFailed, UnsupportedUrl


def _snippets(*texts):
    return [MagicMock(text=t) for t in texts]


def _api(list_result=None, side_effect=None):
    """Patch the module-level class so `.list(video_id)` is controllable."""
    api = MagicMock()
    if side_effect is not None:
        api.list.side_effect = side_effect
    else:
        api.list.return_value = list_result
    return patch.object(video_service, "YouTubeTranscriptApi", return_value=api)


def test_the_declared_dependency_is_installed():
    import importlib.metadata as md

    md.distribution("youtube-transcript-api")  # raises if absent


def test_snippets_are_joined_into_one_transcript():
    transcript = MagicMock()
    transcript.fetch.return_value = _snippets("hello", "world")
    available = MagicMock()
    available.find_transcript.return_value = transcript

    with _api(list_result=available):
        out = video_service._fetch_transcript(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )

    assert out == "hello world"
    available.find_transcript.assert_called_once_with(
        video_service.PREFERRED_LANGUAGES
    )


def test_falls_back_to_any_language_when_no_preferred_one_exists():
    other = MagicMock()
    other.fetch.return_value = _snippets("bonjour")
    available = MagicMock()
    available.find_transcript.side_effect = NoTranscriptFound(
        "vid", ["en"], {}
    )
    available.__iter__.return_value = iter([other])

    with _api(list_result=available):
        out = video_service._fetch_transcript("https://youtu.be/dQw4w9WgXcQ")

    assert out == "bonjour"


def test_captions_turned_off_is_a_422_not_a_500():
    with _api(side_effect=TranscriptsDisabled("dQw4w9WgXcQ")):
        with pytest.raises(UnsupportedUrl) as exc:
            video_service._fetch_transcript("https://youtu.be/dQw4w9WgXcQ")

    assert exc.value.status_code == 422


def test_an_unknown_failure_never_leaks_the_exception_text():
    with _api(side_effect=RuntimeError("connection to 10.0.0.1:443 refused")):
        with pytest.raises(AnalysisFailed) as exc:
            video_service._fetch_transcript("https://youtu.be/dQw4w9WgXcQ")

    assert "10.0.0.1" not in str(exc.value)


def test_a_non_youtube_url_is_rejected_before_any_network_call():
    with _api(list_result=MagicMock()) as api_cls:
        with pytest.raises(UnsupportedUrl):
            video_service._fetch_transcript("https://example.com/not-a-video")
    api_cls.assert_not_called()
