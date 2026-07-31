import uuid
from datetime import datetime, timezone
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import create_app
from tests.conftest import make_token


@pytest.fixture
def api():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = Session(engine)

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    db.close()


def _auth():
    return {"Authorization": f"Bearer {make_token()}"}


def test_upload_audio_exceeds_size_limit(api):
    session_id = uuid.uuid4()
    # Create 6 MB dummy data
    large_audio = b"0" * (6 * 1024 * 1024)
    files = {"audio": ("test.wav", large_audio, "audio/wav")}
    response = api.post(
        f"/interview/sessions/{session_id}/answer",
        headers=_auth(),
        files=files,
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "invalid_audio_upload"
    assert "exceeds" in data["detail"].lower()


def test_upload_audio_invalid_mime_type(api):
    session_id = uuid.uuid4()
    files = {"audio": ("test.txt", b"not audio data", "text/plain")}
    response = api.post(
        f"/interview/sessions/{session_id}/answer",
        headers=_auth(),
        files=files,
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "invalid_audio_upload"
    assert "unsupported audio format" in data["detail"].lower()


def test_upload_audio_empty_file(api):
    session_id = uuid.uuid4()
    files = {"audio": ("empty.wav", b"", "audio/wav")}
    response = api.post(
        f"/interview/sessions/{session_id}/answer",
        headers=_auth(),
        files=files,
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "invalid_audio_upload"
    assert "empty" in data["detail"].lower()


def test_upload_audio_valid_format_calls_service(api):
    session_id = uuid.uuid4()
    files = {"audio": ("good.wav", b"valid audio data", "audio/wav")}
    with patch("app.api.interview.interview_service.answer") as mock_answer:
        # Mocking out the service return value
        from app.models import InterviewSession
        mock_session = InterviewSession(
            id=session_id,
            profile_id=uuid.uuid4(),
            level="Senior",
            job_description="JD",
            cv_text="CV",
            created_at=datetime.now(timezone.utc),
            finished=False,
        )
        mock_answer.return_value = mock_session
        response = api.post(
            f"/interview/sessions/{session_id}/answer",
            headers=_auth(),
            files=files,
        )
        assert response.status_code == 200
        mock_answer.assert_called_once()
