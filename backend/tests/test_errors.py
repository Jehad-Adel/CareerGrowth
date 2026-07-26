from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.errors import AppError, QuotaExceeded
from app.main import create_app


def _client_with(route_fn, path="/boom"):
    app = create_app()
    router = APIRouter()
    router.add_api_route(path, route_fn, methods=["GET"])
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def test_unhandled_error_returns_500_json_with_request_id():
    def boom():
        raise RuntimeError("kaboom")

    r = _client_with(boom).get("/boom")
    assert r.status_code == 500
    body = r.json()
    assert body["detail"] == "Internal server error"
    assert body["request_id"]
    assert "kaboom" not in r.text  # never leak the message


def test_app_error_maps_to_its_status_and_code():
    def boom():
        raise QuotaExceeded("Daily limit reached", feature="cv_analysis", limit=10)

    r = _client_with(boom).get("/boom")
    assert r.status_code == 429
    body = r.json()
    assert body["code"] == "quota_exceeded"
    assert body["detail"] == "Daily limit reached"
    assert body["feature"] == "cv_analysis"
    assert body["limit"] == 10


def test_request_id_echoed_in_header():
    def ok():
        return {"ok": True}

    r = _client_with(ok, path="/ok").get("/ok", headers={"X-Request-ID": "abc123"})
    assert r.headers["X-Request-ID"] == "abc123"


def test_base_app_error_defaults():
    err = AppError("nope")
    assert err.status_code == 400
    assert err.code == "app_error"
