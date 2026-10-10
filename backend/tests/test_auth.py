import jwt
import pytest

from app import auth, db, main, rate_limit
from app.rate_limit import limiter
from app.schemas import User
from tests.conftest import PASSWORD, auth_headers, register


def _analyze(client, headers):
    return client.post(
        "/api/analyze",
        files={"resume": ("cv.md", b"Python", "text/markdown")},
        data={"job_description": "Python"},
        headers=headers,
    )


def test_register_returns_token_and_user(client):
    res = register(client, "New@Example.com")
    assert res.status_code == 201
    body = res.json()
    assert body["user"]["email"] == "new@example.com"
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.json()["email"] == "new@example.com"


def test_duplicate_email_rejected(client):
    register(client, "a@example.com")
    assert register(client, "A@example.com").status_code == 409


@pytest.mark.parametrize("email", ["", "nope", "a@b", "a b@c.de"])
def test_invalid_email_rejected(client, email):
    assert register(client, email).status_code == 400


@pytest.mark.parametrize("password", ["short", "x" * 129])
def test_invalid_password_rejected(client, password):
    assert register(client, password=password).status_code == 400


def test_login_success_and_failures(client):
    register(client, "a@example.com")
    ok = client.post("/api/auth/login", json={"email": "A@example.com", "password": PASSWORD})
    assert ok.status_code == 200 and ok.json()["access_token"]
    wrong = client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrong-password"})
    unknown = client.post("/api/auth/login", json={"email": "z@example.com", "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_password_is_hashed_not_stored(client):
    register(client, "a@example.com")
    stored = db.get_user_by_email("a@example.com")["password_hash"]
    assert PASSWORD not in stored and "$" in stored


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/analyses"),
        ("get", "/api/analyses/1"),
        ("post", "/api/analyze"),
        ("get", "/api/auth/me"),
        ("get", "/api/ping-gemini"),
    ],
)
def test_protected_routes_require_auth(client, method, path):
    assert getattr(client, method)(path).status_code == 401


def test_invalid_expired_and_forged_tokens_rejected(client):
    register(client)
    secret = auth.get_jwt_secret()
    expired = jwt.encode({"sub": "1", "exp": 1}, secret, algorithm="HS256")
    forged = jwt.encode({"sub": "1", "exp": 4102444800}, "other-secret-" + "y" * 32, algorithm="HS256")
    for token in ["garbage", expired, forged]:
        res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401


def test_token_for_unknown_user_rejected(client):
    token = auth.create_access_token(User(id=9999, email="ghost@example.com"))
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_users_cannot_see_each_others_analyses(client, fake_report, monkeypatch):
    monkeypatch.setattr(main, "analyze_resume", lambda *a, **k: fake_report)
    alice = auth_headers(client, "alice@example.com")
    bob = auth_headers(client, "bob@example.com")
    record = _analyze(client, alice).json()

    assert client.get(f"/api/analyses/{record['id']}", headers=alice).status_code == 200
    assert client.get(f"/api/analyses/{record['id']}", headers=bob).status_code == 404
    assert client.get("/api/analyses", headers=bob).json() == []
    assert len(client.get("/api/analyses", headers=alice).json()) == 1


def test_weak_jwt_secret_fails_fast(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "short")
    with pytest.raises(RuntimeError):
        auth.get_jwt_secret()


def test_login_rate_limited_per_ip(client):
    body = {"email": "a@example.com", "password": "bad-password"}
    codes = [client.post("/api/auth/login", json=body).status_code for _ in range(11)]
    assert codes[:10] == [401] * 10
    assert codes[10] == 429


def test_register_rate_limited_per_ip(client):
    codes = [register(client, f"u{i}@example.com").status_code for i in range(6)]
    assert codes[:5] == [201] * 5
    assert codes[5] == 429


def test_analyze_rate_limited_per_user_with_retry_after(client, fake_report, monkeypatch):
    monkeypatch.setattr(main, "analyze_resume", lambda *a, **k: fake_report)
    headers = auth_headers(client)

    assert [_analyze(client, headers).status_code for _ in range(10)] == [200] * 10
    blocked = _analyze(client, headers)
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0

    # another user is unaffected
    other = auth_headers(client, "other@example.com")
    assert _analyze(client, other).status_code == 200


def test_upstream_failures_do_not_use_up_the_analyze_quota(client, fake_report, monkeypatch):
    from fastapi import HTTPException

    def failing(*args, **kwargs):
        raise HTTPException(status_code=502, detail="upstream down")

    monkeypatch.setattr(main, "analyze_resume", failing)
    headers = auth_headers(client)

    assert [_analyze(client, headers).status_code for _ in range(15)] == [502] * 15

    # The quota is still intact for real work once Gemini recovers.
    monkeypatch.setattr(main, "analyze_resume", lambda *a, **k: fake_report)
    assert [_analyze(client, headers).status_code for _ in range(10)] == [200] * 10
    assert _analyze(client, headers).status_code == 429


def test_invalid_input_still_counts_toward_the_quota(client, headers):
    bad = lambda: client.post(  # noqa: E731
        "/api/analyze",
        files={"resume": ("cv.docx", b"x", "application/octet-stream")},
        data={"job_description": "x"},
        headers=headers,
    )
    assert [bad().status_code for _ in range(10)] == [400] * 10
    assert bad().status_code == 429


def test_limiter_refund_gives_back_a_slot():
    limiter.reset()
    assert limiter.check("k", 1, 60) is None
    assert limiter.check("k", 1, 60) is not None
    limiter.refund("k")
    assert limiter.check("k", 1, 60) is None
    limiter.refund("never-seen")  # no-op
    limiter.reset()


def test_limiter_window_expires(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: now[0])
    limiter.reset()
    assert limiter.check("k", 1, 10) is None
    assert limiter.check("k", 1, 10) is not None
    now[0] += 11
    assert limiter.check("k", 1, 10) is None
    limiter.reset()
