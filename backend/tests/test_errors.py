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

    r = _client_with(boom).get(
        "/boom", headers={"X-Request-ID": "myrealid123"}
    )
    assert r.status_code == 500
    body = r.json()
    assert body["detail"] == "Internal server error"
    assert body["request_id"] == "myrealid123"
    assert r.headers["X-Request-ID"] == "myrealid123"
    assert "kaboom" not in r.text  # never leak the message


def test_unhandled_error_still_carries_cors_header():
    def boom():
        raise RuntimeError("kaboom")

    r = _client_with(boom).get(
        "/boom", headers={"Origin": "http://localhost:3000"}
    )
    assert r.status_code == 500
    assert "access-control-allow-origin" in r.headers


def test_app_error_with_colliding_extra_key_does_not_crash():
    def boom():
        raise AppError("boom", code="collides")

    r = _client_with(boom).get("/boom")
    assert r.status_code == 400
    body = r.json()
    assert body["code"] == "app_error"


def test_app_error_extra_cannot_override_reserved_response_keys():
    def boom():
        raise AppError("Safe message", detail="INJECTED", request_id="spoofed")

    r = _client_with(boom).get("/boom")
    body = r.json()
    assert body["detail"] == "Safe message"
    assert body["request_id"] != "spoofed"


def test_invalid_client_request_id_is_replaced():
    def ok():
        return {"ok": True}

    client = _client_with(ok, path="/ok")

    r = client.get("/ok", headers={"X-Request-ID": "a" * 200})
    assert r.headers["X-Request-ID"] != "a" * 200

    r = client.get("/ok", headers={"X-Request-ID": "bad id!"})
    assert r.headers["X-Request-ID"] != "bad id!"


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
