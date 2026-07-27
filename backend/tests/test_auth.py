from tests.conftest import make_token


def test_me_no_token(client):
    assert client.get("/me").status_code == 401


def test_me_bad_signature(client):
    tok = make_token(secret="wrong-secret")
    r = client.get("/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401


def test_me_expired(client):
    tok = make_token(exp_offset=-10)
    r = client.get("/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401


def test_me_valid(client):
    sub = "11111111-1111-1111-1111-111111111111"
    tok = make_token(sub=sub)
    r = client.get("/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == sub
    assert body["email"] == "a@b.com"
