from app.config import get_settings


def test_settings_read_from_env(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "abc123")
    s = get_settings()
    assert s.supabase_jwt_secret == "abc123"
    assert s.cors_origins  # has a default


def test_env_example_lists_required_keys():
    # Single env example lives at the repo root; pytest runs with cwd = backend/
    text = open("../.env.example").read()
    for key in ["DATABASE_URL", "SUPABASE_URL", "SUPABASE_JWT_SECRET", "ANTHROPIC_API_KEY"]:
        assert key in text
