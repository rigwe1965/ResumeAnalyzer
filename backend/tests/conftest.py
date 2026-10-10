import pytest
from fastapi.testclient import TestClient

from app import db, main
from app.schemas import AnalysisReport


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(main, "GEMINI_API_KEY", "test-key")
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def fake_report():
    return AnalysisReport(
        score=72,
        missing_keywords=["Kubernetes"],
        skill_gaps=["Production on-call experience"],
        phrasing_suggestions=["Lead bullets with measurable impact"],
    )
