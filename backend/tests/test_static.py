import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.static import mount_frontend


@pytest.fixture
def site(tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>app</html>")
    (dist / "assets" / "app.js").write_text("console.log(1)")
    (dist / "favicon.svg").write_text("<svg/>")
    (tmp_path / "secret.txt").write_text("top secret")

    app = FastAPI()

    @app.get("/api/ping")
    def ping():
        return {"ok": True}

    assert mount_frontend(app, dist) is True
    return TestClient(app)


def test_serves_index_and_spa_fallback(site):
    assert "app" in site.get("/").text
    assert "app" in site.get("/some/client/route").text


def test_serves_assets_and_root_files(site):
    assert site.get("/assets/app.js").text == "console.log(1)"
    assert site.get("/favicon.svg").text == "<svg/>"


def test_api_routes_still_work_and_unknown_api_is_json_404(site):
    assert site.get("/api/ping").json() == {"ok": True}
    res = site.get("/api/nope")
    assert res.status_code == 404
    assert res.headers["content-type"].startswith("application/json")


@pytest.mark.parametrize("path", ["/../secret.txt", "/%2e%2e/secret.txt", "/..%2fsecret.txt"])
def test_path_traversal_does_not_leak_files(site, path):
    assert "top secret" not in site.get(path).text


def test_missing_directory_is_a_noop(tmp_path):
    assert mount_frontend(FastAPI(), tmp_path / "missing") is False
