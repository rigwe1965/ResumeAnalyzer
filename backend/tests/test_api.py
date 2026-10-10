from app import main


def _post(client, filename="cv.md", content=b"Python developer", jd="Needs Python"):
    return client.post(
        "/api/analyze",
        files={"resume": (filename, content, "text/markdown")},
        data={"job_description": jd},
    )


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_analyze_saves_and_returns_record(client, fake_report, monkeypatch):
    monkeypatch.setattr(main, "analyze_resume", lambda *args, **kwargs: fake_report)

    res = _post(client)

    assert res.status_code == 200
    body = res.json()
    assert body["score"] == 72
    assert body["resume_filename"] == "cv.md"
    assert body["missing_keywords"] == ["Kubernetes"]

    listing = client.get("/api/analyses").json()
    assert [row["id"] for row in listing] == [body["id"]]
    assert client.get(f"/api/analyses/{body['id']}").json() == body


def test_history_is_newest_first(client, fake_report, monkeypatch):
    monkeypatch.setattr(main, "analyze_resume", lambda *args, **kwargs: fake_report)
    first = _post(client).json()["id"]
    second = _post(client).json()["id"]

    assert [row["id"] for row in client.get("/api/analyses").json()] == [second, first]


def test_missing_analysis_is_404(client):
    assert client.get("/api/analyses/999").status_code == 404


def test_empty_job_description_rejected(client):
    assert _post(client, jd="   ").status_code == 400


def test_overlong_job_description_rejected(client):
    assert _post(client, jd="x" * (main.MAX_JOB_DESCRIPTION_CHARS + 1)).status_code == 413


def test_unsupported_file_rejected(client):
    assert _post(client, filename="cv.docx").status_code == 400


def test_missing_api_key_returns_500(client, monkeypatch):
    monkeypatch.setattr(main, "GEMINI_API_KEY", None)
    assert _post(client).status_code == 500
