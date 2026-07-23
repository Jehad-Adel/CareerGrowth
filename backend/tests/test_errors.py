from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.main import create_app


def test_unhandled_error_returns_500_json():
    app = create_app()
    router = APIRouter()

    @router.get("/boom")
    def boom():
        raise RuntimeError("kaboom")

    app.include_router(router)
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/boom")
    assert r.status_code == 500
    assert r.json() == {"detail": "Internal server error"}
