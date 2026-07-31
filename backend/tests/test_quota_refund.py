import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db import Base
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


def test_refund_decrements_calls():
    db, profile = _session_and_profile()
    feature = "cv_analysis"

    count1 = quota_service.consume(db, profile.id, feature)
    assert count1 == 1

    count2 = quota_service.refund(db, profile.id, feature)
    assert count2 == 0

    # Refunding at 0 stays at 0
    count3 = quota_service.refund(db, profile.id, feature)
    assert count3 == 0


def test_consume_and_refund_on_error():
    db, profile = _session_and_profile()
    feature = "cv_analysis"

    with pytest.raises(RuntimeError):
        with quota_service.consume_and_refund_on_error(db, profile.id, feature):
            raise RuntimeError("LLM failed")

    usage = quota_service.usage_today(db, profile.id)
    assert usage.get(feature, 0) == 0


def test_consume_and_refund_on_success():
    db, profile = _session_and_profile()
    feature = "cv_analysis"

    with quota_service.consume_and_refund_on_error(db, profile.id, feature):
        pass  # Successful execution

    usage = quota_service.usage_today(db, profile.id)
    assert usage[feature] == 1
