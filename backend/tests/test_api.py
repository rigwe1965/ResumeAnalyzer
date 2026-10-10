from app import main


def _post(client, headers, filename="cv.md", content=b"Python developer", jd="Needs Python"):
    return client.post(
        "/api/analyze",
        files={"resume": (filename, content, "text/markdown")},
        data={"job_description": jd},
        headers=headers,
    )


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_analyze_saves_and_returns_record(client, headers, fake_report, monkeypatch):
    monkeypatch.setattr(main, "analyze_resume", lambda *args, **kwargs: fake_report)

    res = _post(client, headers)

    assert res.status_code == 200
    body = res.json()
    assert body["score"] == 72
    assert body["resume_filename"] == "cv.md"
    assert body["missing_keywords"] == ["Kubernetes"]

    listing = client.get("/api/analyses", headers=headers).json()
    assert [row["id"] for row in listing] == [body["id"]]
    assert client.get(f"/api/analyses/{body['id']}", headers=headers).json() == body


def test_history_is_newest_first(client, headers, fake_report, monkeypatch):
    monkeypatch.setattr(main, "analyze_resume", lambda *args, **kwargs: fake_report)
    first = _post(client, headers).json()["id"]
    second = _post(client, headers).json()["id"]

    ids = [row["id"] for row in client.get("/api/analyses", headers=headers).json()]
    assert ids == [second, first]


def test_missing_analysis_is_404(client, headers):
    assert client.get("/api/analyses/999", headers=headers).status_code == 404


def test_empty_job_description_rejected(client, headers):
    assert _post(client, headers, jd="   ").status_code == 400


def test_overlong_job_description_rejected(client, headers):
    assert _post(client, headers, jd="x" * (main.MAX_JOB_DESCRIPTION_CHARS + 1)).status_code == 413


def test_unsupported_file_rejected(client, headers):
    assert _post(client, headers, filename="cv.docx").status_code == 400


def test_missing_api_key_returns_500(client, headers, monkeypatch):
    monkeypatch.setattr(main, "GEMINI_API_KEY", None)
    assert _post(client, headers).status_code == 500
