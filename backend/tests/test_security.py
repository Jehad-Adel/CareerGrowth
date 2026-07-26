from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.limiter import client_key, limiter
from app.main import create_app


def test_security_headers_present(client):
    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'none'" in r.headers["Content-Security-Policy"]


def test_hsts_only_in_production(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ENVIRONMENT", "development")
    dev = TestClient(create_app())
    assert "Strict-Transport-Security" not in dev.get("/health").headers

    get_settings.cache_clear()
    monkeypatch.setenv("ENVIRONMENT", "production")
    prod = TestClient(create_app())
    assert "max-age=" in prod.get("/health").headers["Strict-Transport-Security"]


def test_docs_disabled_in_production(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ENVIRONMENT", "production")
    prod = TestClient(create_app())
    assert prod.get("/docs").status_code == 404
    assert prod.get("/openapi.json").status_code == 404


def test_docs_enabled_in_development(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ENVIRONMENT", "development")
    dev = TestClient(create_app())
    assert dev.get("/openapi.json").status_code == 200


# --- Rate limiting -----------------------------------------------------


def test_global_rate_limit_enforced_on_real_route(client):
    responses = [client.get("/health") for _ in range(125)]
    statuses = [r.status_code for r in responses]
    assert 429 in statuses

    blocked = responses[statuses.index(429)]
    assert "Retry-After" in blocked.headers
    assert blocked.json()["code"] == "rate_limited"


def test_rate_limit_body_leaks_nothing(client):
    responses = [client.get("/health") for _ in range(125)]
    blocked = next(r for r in responses if r.status_code == 429)
    body = blocked.json()

    assert set(body.keys()) == {"detail", "code"}
    # No client key, no header echo, no exception/traceback text.
    for value in body.values():
        assert "testclient" not in str(value)
        assert "X-Forwarded-For" not in str(value)
        assert "Traceback" not in str(value)


def test_decorated_route_rate_limit_enforced():
    """Proves the @limiter.limit(...) decorator path works standalone.

    Phase 3 depends on this for the CV upload route; it does not rely on
    SlowAPIMiddleware's (broken) route-table walk.
    """
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.get("/decorated")
    @limiter.limit("3/minute")
    def decorated(request: Request):
        return {"ok": True}

    test_client = TestClient(app)
    statuses = [test_client.get("/decorated").status_code for _ in range(4)]
    assert statuses == [200, 200, 200, 429]


def test_rate_limit_budget_resets_between_tests_a(client):
    for _ in range(119):
        assert client.get("/health").status_code == 200


def test_rate_limit_budget_resets_between_tests_b(client):
    # If the conftest reset didn't run, this would inherit leftover budget
    # consumed by test_a above (same process, same module-level storage)
    # and start failing partway through.
    for _ in range(119):
        assert client.get("/health").status_code == 200


def _make_request(headers=None, client_host="1.2.3.4"):
    headers = headers or {}
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [
            (k.lower().encode(), v.encode()) for k, v in headers.items()
        ],
        "client": (client_host, 12345),
        "query_string": b"",
    }
    return Request(scope)


def test_client_key_ignores_xff_by_default(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("TRUSTED_PROXY_COUNT", "0")
    req = _make_request(
        {"X-Forwarded-For": "9.9.9.9, 8.8.8.8"}, client_host="1.2.3.4"
    )
    assert client_key(req) == "1.2.3.4"


def test_client_key_uses_nth_from_right_when_trusted(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("TRUSTED_PROXY_COUNT", "1")
    req = _make_request(
        {"X-Forwarded-For": "9.9.9.9, 8.8.8.8, 7.7.7.7"}, client_host="1.2.3.4"
    )
    assert client_key(req) == "7.7.7.7"


def test_client_key_falls_back_when_header_shorter_than_trusted_count(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("TRUSTED_PROXY_COUNT", "2")
    req = _make_request({"X-Forwarded-For": "9.9.9.9"}, client_host="1.2.3.4")
    assert client_key(req) == "1.2.3.4"
