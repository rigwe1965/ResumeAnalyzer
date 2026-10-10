import pytest
from fastapi import HTTPException

from app import gemini_client
from app.schemas import AnalysisReport


class FakeModels:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def generate_content(self, **kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeClient:
    def __init__(self, outcomes):
        self.models = FakeModels(outcomes)


class FakeResponse:
    def __init__(self, parsed=None, text=None):
        self.parsed = parsed
        self.text = text


REPORT = AnalysisReport(score=50, missing_keywords=[], skill_gaps=[], phrasing_suggestions=[])


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(gemini_client.time, "sleep", lambda _: None)


def test_prompt_survives_braces_in_user_text():
    prompt = gemini_client.build_prompt("resume {x} {resume_text}", "jd {y}")
    assert "resume {x}" in prompt and "jd {y}" in prompt


def test_retries_then_succeeds():
    client = FakeClient([RuntimeError("boom"), FakeResponse(parsed=REPORT)])
    assert gemini_client.analyze_resume(client, "m", "r", "j") == REPORT
    assert client.models.calls == 2


def test_gives_up_after_max_attempts_without_leaking_error():
    client = FakeClient([RuntimeError("secret-detail")] * gemini_client.MAX_ATTEMPTS)
    with pytest.raises(HTTPException) as exc:
        gemini_client.analyze_resume(client, "m", "r", "j")
    assert exc.value.status_code == 502
    assert "secret-detail" not in exc.value.detail


def test_falls_back_to_json_text():
    client = FakeClient([FakeResponse(parsed=None, text=REPORT.model_dump_json())])
    assert gemini_client.analyze_resume(client, "m", "r", "j") == REPORT


def test_unparseable_response_is_502():
    client = FakeClient([FakeResponse(parsed=None, text="not json")])
    with pytest.raises(HTTPException) as exc:
        gemini_client.analyze_resume(client, "m", "r", "j")
    assert exc.value.status_code == 502
