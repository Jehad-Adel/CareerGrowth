from app.config import get_settings


def test_settings_read_from_env(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("SUPABASE_URL", "https://abc123.supabase.co")
    s = get_settings()
    assert s.supabase_url == "https://abc123.supabase.co"
    assert s.cors_origins  # has a default


def test_env_example_lists_required_keys():
    # Single env example lives at the repo root; pytest runs with cwd = backend/
    text = open("../.env.example").read()
    for key in ["DATABASE_URL", "DIRECT_DATABASE_URL", "SUPABASE_URL", "GOOGLE_API_KEY"]:
        assert key in text
    # Supabase signs with ES256 keys fetched from JWKS; there is no shared
    # secret to configure, and leaving a dead variable in the example invites
    # someone to go looking for a value that does not exist.
    assert "SUPABASE_JWT_SECRET" not in text


def test_environment_defaults_to_development(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    s = get_settings()
    assert s.environment == "development"
    assert s.is_production is False


def test_is_production_when_environment_is_production(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ENVIRONMENT", "production")
    s = get_settings()
    assert s.is_production is True


def test_cors_origin_list_strips_blanks_and_slashes(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("CORS_ORIGINS", "https://a.com/, ,https://b.com")
    assert get_settings().cors_origin_list == ["https://a.com", "https://b.com"]
