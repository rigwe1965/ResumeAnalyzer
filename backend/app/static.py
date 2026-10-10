from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def mount_frontend(app: FastAPI, directory: Path) -> bool:
    """Serve a built single-page frontend from `directory`. Call after all API routes are
    registered. Returns False (and does nothing) if the directory has no index.html."""
    directory = directory.resolve()
    index = directory / "index.html"
    if not index.is_file():
        return False

    assets = directory / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        # Unknown API paths should 404 as JSON, not fall through to the HTML app.
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found.")

        candidate = (directory / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(directory):
            return FileResponse(candidate)
        return FileResponse(index)

    return True
