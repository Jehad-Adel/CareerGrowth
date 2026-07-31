import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.errors import QuotaExceeded
from app.models import CareerProfile
from app.services import quota_service


def _session_and_profile():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    profile = CareerProfile(user_id=uuid.uuid4())
    db.add(profile)
    db.commit()
    return db, profile


def test_consume_increments_and_returns_count():
    db, profile = _session_and_profile()
    assert quota_service.consume(db, profile.id, "cv_analysis") == 1
    assert quota_service.consume(db, profile.id, "cv_analysis") == 2


def test_consume_raises_once_limit_is_reached(monkeypatch):
    db, profile = _session_and_profile()
    monkeypatch.setitem(quota_service.DAILY_LIMITS, "cv_analysis", 2)

    quota_service.consume(db, profile.id, "cv_analysis")
    quota_service.consume(db, profile.id, "cv_analysis")
    with pytest.raises(QuotaExceeded) as exc:
        quota_service.consume(db, profile.id, "cv_analysis")

    assert exc.value.extra["feature"] == "cv_analysis"
    assert exc.value.extra["limit"] == 2
    assert exc.value.status_code == 429


def test_a_rejected_call_is_not_counted(monkeypatch):
    """Being over the limit must not keep inflating the counter."""
    db, profile = _session_and_profile()
    monkeypatch.setitem(quota_service.DAILY_LIMITS, "cv_analysis", 1)

    quota_service.consume(db, profile.id, "cv_analysis")
    for _ in range(3):
        with pytest.raises(QuotaExceeded):
            quota_service.consume(db, profile.id, "cv_analysis")

    assert quota_service.usage_today(db, profile.id) == {"cv_analysis": 1}


def test_features_have_independent_budgets(monkeypatch):
    db, profile = _session_and_profile()
    monkeypatch.setitem(quota_service.DAILY_LIMITS, "cv_analysis", 1)
    quota_service.consume(db, profile.id, "cv_analysis")
    assert quota_service.consume(db, profile.id, "job_match") == 1


def test_profiles_have_independent_budgets(monkeypatch):
    db, profile = _session_and_profile()
    other = CareerProfile(user_id=uuid.uuid4())
    db.add(other)
    db.commit()
    monkeypatch.setitem(quota_service.DAILY_LIMITS, "cv_analysis", 1)

    quota_service.consume(db, profile.id, "cv_analysis")
    assert quota_service.consume(db, other.id, "cv_analysis") == 1


def test_unknown_feature_is_a_programming_error():
    db, profile = _session_and_profile()
    with pytest.raises(ValueError, match="Unknown AI feature"):
        quota_service.consume(db, profile.id, "not_a_feature")


def test_usage_today_reports_per_feature_counts():
    db, profile = _session_and_profile()
    quota_service.consume(db, profile.id, "cv_analysis")
    quota_service.consume(db, profile.id, "job_match")
    quota_service.consume(db, profile.id, "job_match")
    assert quota_service.usage_today(db, profile.id) == {
        "cv_analysis": 1,
        "job_match": 2,
    }


def test_usage_today_is_empty_for_a_fresh_profile():
    db, profile = _session_and_profile()
    assert quota_service.usage_today(db, profile.id) == {}


def test_yesterdays_usage_does_not_count_against_today(monkeypatch):
    db, profile = _session_and_profile()
    monkeypatch.setitem(quota_service.DAILY_LIMITS, "cv_analysis", 1)

    from datetime import timedelta

    real_today = quota_service._today()
    monkeypatch.setattr(
        quota_service, "_today", lambda: real_today - timedelta(days=1)
    )
    quota_service.consume(db, profile.id, "cv_analysis")

    monkeypatch.setattr(quota_service, "_today", lambda: real_today)
    assert quota_service.consume(db, profile.id, "cv_analysis") == 1


def test_every_service_feature_has_a_limit():
    """Every feature key any service charges against must exist in DAILY_LIMITS.

    `consume` raises a bare ValueError on an unknown feature, which is not an
    AppError and so leaves the client with a blanket 500 that names nothing.
    Quiz, video, and offer evaluation all shipped that way: their FEATURE
    constants were never added here, so all three features 500'd on every
    single request while the suite stayed green.

    Two shapes are collected, because services use both:
      - a module-level `FEATURE = "..."` constant (most services)
      - a string literal passed straight to `consume` /
        `consume_and_refund_on_error` (roadmap_service passes "roadmap")

    A feature resolved from a variable (matching_service passes its callers'
    literals through an `_invoke(feature=...)` parameter) cannot be read
    statically; those literals are caught as arguments at the call sites.
    """
    import ast
    import pathlib

    services = pathlib.Path(quota_service.__file__).parent
    charged: dict[str, str] = {}

    for path in sorted(services.glob("*.py")):
        if path.name == "quota_service.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            # FEATURE = "..."
            if isinstance(node, ast.Assign) and isinstance(
                node.value, ast.Constant
            ):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "FEATURE":
                        charged[node.value.value] = path.name

            # consume(db, profile_id, "literal")
            if isinstance(node, ast.Call):
                name = getattr(node.func, "attr", None) or getattr(
                    node.func, "id", None
                )
                if name in {"consume", "consume_and_refund_on_error"}:
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(
                            arg.value, str
                        ):
                            charged[arg.value] = path.name

    assert charged, "found no AI features to check — the scan itself is broken"

    missing = {
        feature: module
        for feature, module in sorted(charged.items())
        if feature not in quota_service.DAILY_LIMITS
    }
    assert not missing, (
        "these services charge quota against features with no entry in "
        f"DAILY_LIMITS, so every call 500s: {missing}"
    )
