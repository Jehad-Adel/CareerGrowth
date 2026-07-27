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
