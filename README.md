# Resume Analyzer

Upload a resume (`.pdf` or `.md`) and paste a job description. Gemini scores the fit and
returns missing keywords, skill gaps, and phrasing suggestions. Analyses are saved per user
in SQLite and browsable in a history view.

**Stack:** FastAPI · React (Vite) · Gemini API · SQLite

## Configuration

Copy `backend/.env.example` to `backend/.env` and fill it in:

| Variable | Required | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | yes | Gemini API key |
| `JWT_SECRET` | yes | Random string, 32+ chars. `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `GEMINI_MODEL` | no | Defaults to `gemini-3.8-flash` |
| `CORS_ORIGINS` | no | Comma-separated browser origins (default `http://localhost:5173`). Not needed when the app serves its own frontend. |
| `JWT_EXPIRE_MINUTES` | no | Token lifetime, default 720 |
| `DATABASE_PATH` | no | SQLite file location (default `backend/data/resume_analyzer.db`) |
| `STATIC_DIR` | no | Built frontend to serve (default `frontend/dist`) |

## Run with Docker

```sh
docker compose up --build
```

Open <http://localhost:8000>. One container serves the API and the built frontend; the
database lives in the `app-data` volume.

The app keeps rate-limit counters in process memory, so run a **single worker/replica**. If
you put a reverse proxy in front, set `FORWARDED_ALLOW_IPS` to the proxy's address so rate
limits apply to real client IPs.

## Run for development

```sh
# backend (http://localhost:8000)
cd backend
python -m venv .venv && .venv\Scripts\activate      # source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload --reload-dir app

# frontend (http://localhost:5173, proxies /api to :8000)
cd frontend
npm ci
npm run dev
```

## Tests and CI

```sh
cd backend && python -m pytest
cd frontend && npm run build
```

GitHub Actions (`.github/workflows/ci.yml`) runs the backend tests, the frontend build, and
a Docker build plus container smoke test on every pull request and push to `main`.

## API

All routes except `/api/health` and `/api/auth/*` require `Authorization: Bearer <token>`.

| Method | Path | Notes |
|---|---|---|
| POST | `/api/auth/register` | `{email, password}` → token. 5/hour per IP |
| POST | `/api/auth/login` | `{email, password}` → token. 10/15 min per IP |
| GET | `/api/auth/me` | Current user |
| POST | `/api/analyze` | multipart: `resume` file + `job_description`. 10/hour per user |
| GET | `/api/analyses` | Your analyses, newest first |
| GET | `/api/analyses/{id}` | One analysis |
| GET | `/api/health` | Liveness check |
