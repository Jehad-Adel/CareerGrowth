from fastapi.testclient import TestClient

from app.config import get_settings
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
