import jwt
import pytest

from tests.conftest import WRONG_SIGNING_KEY, make_token


def test_me_no_token(client):
    assert client.get("/me").status_code == 401


def test_me_bad_signature(client):
    """Signed with a key the JWKS endpoint does not publish."""
    tok = make_token(key=WRONG_SIGNING_KEY)
    r = client.get("/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401


def test_me_expired(client):
    tok = make_token(exp_offset=-10)
    r = client.get("/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401


def test_me_wrong_audience(client):
    tok = make_token(aud="anon")
    r = client.get("/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401


def test_me_rejects_a_token_with_no_subject(client):
    from tests.conftest import TEST_KID, TEST_SIGNING_KEY

    tok = jwt.encode(
        {"aud": "authenticated", "exp": 9999999999, "email": "a@b.com"},
        TEST_SIGNING_KEY,
        algorithm="ES256",
        headers={"kid": TEST_KID},
    )
    r = client.get("/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401


def test_me_rejects_an_unsigned_token(client):
    """alg:none must never be accepted."""
    tok = jwt.encode(
        {"sub": "x", "aud": "authenticated", "exp": 9999999999},
        key="",
        algorithm="none",
    )
    r = client.get("/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401


def test_me_rejects_garbage(client):
    r = client.get("/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


def test_me_valid(client):
    sub = "11111111-1111-1111-1111-111111111111"
    tok = make_token(sub=sub)
    r = client.get("/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == sub
    assert body["email"] == "a@b.com"


@pytest.mark.parametrize("bad", ["Invalid token", "Missing bearer token"])
def test_401_body_never_explains_why(client, bad):
    """The reason must not distinguish expired from wrongly-signed."""
    expired = client.get(
        "/me", headers={"Authorization": f"Bearer {make_token(exp_offset=-10)}"}
    ).json()["detail"]
    forged = client.get(
        "/me",
        headers={"Authorization": f"Bearer {make_token(key=WRONG_SIGNING_KEY)}"},
    ).json()["detail"]
    assert expired == forged


def test_token_from_another_supabase_project_is_rejected(client):
    """A valid signature is not enough -- `iss` must name this project.

    Redundant with the JWKS pin in practice, since a foreign project's key is
    never served by this project's JWKS. It matters if SUPABASE_URL is ever
    pointed somewhere else by mistake.
    """
    tok = make_token(iss="https://someone-elses-project.supabase.co/auth/v1")
    r = client.get("/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401


@pytest.mark.parametrize("claim", ["exp", "sub", "aud", "iss"])
def test_token_missing_a_required_claim_is_rejected(client, claim):
    """PyJWT validates these when present but does not require them.

    A token minted without `exp` would otherwise verify forever, and one
    without `sub` has nothing tying it to a profile.
    """
    import time
    import uuid as _uuid

    import jwt

    from tests.conftest import TEST_KID, TEST_SIGNING_KEY

    payload = {
        "sub": str(_uuid.uuid4()),
        "email": "a@b.com",
        "aud": "authenticated",
        "iss": "http://localhost/auth/v1",
        "exp": int(time.time()) + 3600,
    }
    del payload[claim]

    tok = jwt.encode(
        payload, TEST_SIGNING_KEY, algorithm="ES256", headers={"kid": TEST_KID}
    )
    r = client.get("/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401
