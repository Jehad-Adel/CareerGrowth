import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import create_app
from tests.conftest import make_token


@pytest.fixture
def api():
    # TestClient runs the app on a worker thread, so the session must be
    # usable off the creating thread; StaticPool keeps every connection
    # pointed at the same in-memory database, which otherwise vanishes
    # (taking the schema with it) the moment a second connection opens.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = Session(engine)

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    db.close()


def _auth(sub=None):
    return {"Authorization": f"Bearer {make_token(sub=sub)}"}


def test_profile_requires_auth(api):
    assert api.get("/profile").status_code == 401


def test_profile_rejects_a_bad_signature(api):
    from tests.conftest import WRONG_SIGNING_KEY

    tok = make_token(key=WRONG_SIGNING_KEY)
    r = api.get("/profile", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401


def test_get_profile_creates_it_on_first_call(api):
    headers = _auth()
    r = api.get("/profile", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["level"] == 1
    assert body["xp"] == 0
    assert body["level_title"] == "Seedling"
    assert body["has_cv"] is False
    assert "cv_text" not in body  # never ship the raw CV to the client

    again = api.get("/profile", headers=headers)
    assert again.json()["id"] == body["id"]


def test_two_users_get_separate_profiles(api):
    a = api.get("/profile", headers=_auth("11111111-1111-1111-1111-111111111111"))
    b = api.get("/profile", headers=_auth("22222222-2222-2222-2222-222222222222"))
    assert a.json()["id"] != b.json()["id"]


def test_patch_profile(api):
    headers = _auth()
    api.get("/profile", headers=headers)
    r = api.patch("/profile", headers=headers, json={"target_role": "Staff Engineer"})
    assert r.status_code == 200
    assert r.json()["target_role"] == "Staff Engineer"


def test_patch_profile_requires_auth(api):
    assert api.patch("/profile", json={"target_role": "x"}).status_code == 401


def test_patch_profile_rejects_an_overlong_field(api):
    headers = _auth()
    api.get("/profile", headers=headers)
    r = api.patch("/profile", headers=headers, json={"target_role": "x" * 300})
    assert r.status_code == 422


def test_post_and_get_skills(api):
    headers = _auth()
    api.get("/profile", headers=headers)

    r = api.post(
        "/profile/skills",
        headers=headers,
        json={"skills": [{"name": "Python", "mastery": 60}]},
    )
    assert r.status_code == 200

    skills = api.get("/profile/skills", headers=headers).json()
    assert [s["name"] for s in skills] == ["Python"]
    assert skills[0]["source"] == "manual"
    assert skills[0]["mastery"] == 60


def test_skills_are_scoped_to_the_caller(api):
    a = _auth("33333333-3333-3333-3333-333333333333")
    b = _auth("44444444-4444-4444-4444-444444444444")

    api.get("/profile", headers=a)
    api.get("/profile", headers=b)
    api.post("/profile/skills", headers=a, json={"skills": [{"name": "Python"}]})

    assert api.get("/profile/skills", headers=b).json() == []


def test_post_skills_rejects_an_empty_list(api):
    headers = _auth()
    api.get("/profile", headers=headers)
    assert api.post("/profile/skills", headers=headers, json={"skills": []}).status_code == 422


def test_post_skills_rejects_an_unbounded_list(api):
    """One request must not be able to create unbounded rows."""
    headers = _auth()
    api.get("/profile", headers=headers)
    payload = {"skills": [{"name": f"skill-{i}"} for i in range(101)]}
    assert api.post("/profile/skills", headers=headers, json=payload).status_code == 422


def test_posting_the_same_skill_twice_does_not_duplicate_it(api):
    headers = _auth()
    api.get("/profile", headers=headers)
    api.post("/profile/skills", headers=headers, json={"skills": [{"name": "Go"}]})
    api.post("/profile/skills", headers=headers, json={"skills": [{"name": "go"}]})

    assert len(api.get("/profile/skills", headers=headers).json()) == 1


def test_skills_endpoints_require_auth(api):
    assert api.get("/profile/skills").status_code == 401
    assert api.post("/profile/skills", json={"skills": [{"name": "x"}]}).status_code == 401
