from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import get_db
from app.main import create_app


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "ok"}


def test_health_reports_degraded_when_db_is_down():
    class BrokenSession:
        def execute(self, *_args, **_kwargs):
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    app = create_app()
    app.dependency_overrides[get_db] = lambda: BrokenSession()
    r = TestClient(app).get("/health")

    assert r.status_code == 503
    assert r.json()["status"] == "degraded"
    assert r.json()["database"] == "error"
    # A public probe must not describe the failure.
    assert "connection refused" not in r.text
    assert "SELECT 1" not in r.text
