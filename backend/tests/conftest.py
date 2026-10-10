import pytest
from fastapi.testclient import TestClient

from app import db, main
from app.rate_limit import limiter
from app.schemas import AnalysisReport

PASSWORD = "correct-horse-battery"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret-" + "x" * 32)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(main, "GEMINI_API_KEY", "test-key")
    limiter.reset()
    with TestClient(main.app) as test_client:
        yield test_client
    limiter.reset()


def register(client, email="user@example.com", password=PASSWORD):
    return client.post("/api/auth/register", json={"email": email, "password": password})


def auth_headers(client, email="user@example.com"):
    token = register(client, email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def headers(client):
    return auth_headers(client)


@pytest.fixture
def fake_report():
    return AnalysisReport(
        score=72,
        missing_keywords=["Kubernetes"],
        skill_gaps=["Production on-call experience"],
        phrasing_suggestions=["Lead bullets with measurable impact"],
    )
