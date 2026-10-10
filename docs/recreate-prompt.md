# Prompt to recreate Resume Analyzer

Paste the prompt below into a fresh Claude Code session in an empty folder. It describes the app
as it stands today (auth, rate limiting, Docker, CI, green/white theme included).

---

Build "Resume Analyzer": a full-stack web app where signed-in users upload a resume and a job
description, and Gemini scores the fit and suggests improvements. Analyses are saved per user
and browsable in a history view. Build it end to end, write tests, and verify that it runs.
Use `git init` and make small, meaningful commits.

## Stack
- Backend: Python 3.11, FastAPI, SQLite (stdlib `sqlite3`), `google-genai` SDK, `pypdf`,
  `PyJWT`, `python-dotenv`, `python-multipart`. Pin versions in `backend/requirements.txt`;
  put pytest in `backend/requirements-dev.txt`.
- Frontend: React + Vite, plain CSS (no component library), `fetch` through a small `api.js` wrapper.
- Layout: `backend/app/`, `backend/tests/`, `frontend/`, plus `Dockerfile`, `docker-compose.yml`,
  `.github/workflows/ci.yml`, and `README.md` at the repo root.

## Backend behavior
Config comes from `backend/.env` (load it when the `app` package is imported; commit only
`.env.example`, never real keys): `GEMINI_API_KEY`, `GEMINI_MODEL` (default `gemini-3.8-flash`;
confirm the current model name against Google's docs), `JWT_SECRET` (required, 32+ chars, reject
placeholder values, fail fast at startup), `JWT_EXPIRE_MINUTES` (default 720), `CORS_ORIGINS`
(default `http://localhost:5173`), `DATABASE_PATH`, and `STATIC_DIR`.

Endpoints (all JSON unless noted):
- `GET /api/health` is public.
- `POST /api/auth/register` and `POST /api/auth/login` take `{email, password}` and return
  `{access_token, token_type, user}`. Emails are normalized to lowercase and validated;
  passwords are 8–128 chars. Hash with stdlib `hashlib.scrypt` and a per-user salt. Duplicate
  email gives 409. A wrong password and an unknown email must return the identical 401 and do
  equal work, so timing doesn't reveal which emails exist.
- `GET /api/auth/me` returns the current user.
- `POST /api/analyze` takes multipart `resume` (.pdf or .md) plus `job_description`, returns the
  saved analysis, and requires auth.
- `GET /api/analyses` lists the current user's analyses, newest first, as id, filename, score and
  created_at.
- `GET /api/analyses/{id}` returns one full analysis. Another user's record must return 404.
- `GET /api/ping-gemini` is an authenticated smoke test.

Analysis rules:
- Gemini returns structured JSON via `response_schema`: `score` (int 0–100),
  `missing_keywords`, `skill_gaps`, `phrasing_suggestions` (lists of strings).
- Prompt-injection hardening: wrap the resume and job description in tagged sections, tell the
  model they are untrusted data, and build the prompt with `str.replace`, not `str.format`.
- Input limits: resume file ≤ 5 MB (read in a bounded way), PDF ≤ 20 pages and must start with
  `%PDF`, extracted text ≤ 50,000 chars, markdown must be valid UTF-8, job description ≤ 20,000
  chars. Scanned/image-only PDFs get a clear "no text could be extracted" error.
- Gemini call: 60 s timeout; retry up to 3 times with backoff only for timeouts, connection
  errors, and HTTP 408/429/500/502/503/504. Permanent errors such as 402, 401 and 400 fail on the
  first attempt. Log details server-side and return a generic 502 message, never raw upstream errors.
- Run blocking endpoints as plain `def` so FastAPI uses its threadpool.

Rate limiting (in-memory sliding window, thread-safe, with `Retry-After` on 429):
register 5/hour per IP; login 10/15 min per IP; analyze 10/hour per user; history, detail and
`/me` 120/min per user; ping 5/hour per user. When Gemini fails (502), refund the user's analyze
slot. Invalid input still counts. Document that this is per-process and that a reverse proxy
needs `FORWARDED_ALLOW_IPS`.

Database: tables `users` (unique email, password hash) and `analyses` (user_id, filename, resume
text, job description, score, JSON-encoded list columns, created_at). Create them at startup with
a lifespan handler, close connections properly, and add an index on (user_id, created_at). If an
older DB lacks `user_id`, migrate it with `ALTER TABLE`.

Serving: if the built frontend exists, serve it from FastAPI at `/` with an SPA fallback, serve
`/assets`, guard against path traversal, and keep unknown `/api/*` paths as JSON 404s.

## Frontend behavior
- Login/register form, with the token kept in `localStorage`. Restore the session on load via
  `/api/auth/me`. Show the signed-in email with a Sign out link. On any 401, return to the login
  screen. On 429, show a friendly "try again in about N min" message from `Retry-After`.
- Two tabs after login. **Analyze**: file input (.pdf/.md), job description textarea, submit,
  then a report view with the score, missing keywords, skill gaps and phrasing suggestions.
  **History**: a list of past analyses; clicking one shows its report.
- Visual theme: a "redlined document" look: serif body text (Source Serif 4), a handwritten
  accent font (Kalam) for markup details such as the score stamp, keyword underlines and margin
  carets, with a paper-sheet page under folder-style tabs. Colors are brand green and white. All
  colors are CSS custom properties in `index.css` (`--brand` is `#0f7a3d`, plus `--paper`,
  `--ink`, `--rule`, `--danger`), with a `prefers-color-scheme: dark` override. Errors and low
  scores use the red `--danger` color, and good scores use the brand green. Include a green
  document favicon and a theme-color meta tag. Respect `prefers-reduced-motion`.

## Deployment and CI
- Multi-stage `Dockerfile`: a Node 22 stage builds the frontend, then a Python 3.11-slim stage
  runs uvicorn as a non-root user with a `/data` volume, a `HEALTHCHECK` on `/api/health`, and a
  single worker (the limiter is in memory).
- `docker-compose.yml` reads `backend/.env`, publishes port 8000, and mounts a named volume.
  Add a `.dockerignore` that excludes `.env`, venvs, node_modules and the local DB.
- GitHub Actions on pull requests and pushes to `main`, with current action versions and
  `ubuntu-24.04`: a backend job (pytest), a frontend job (`npm ci`, `npm run build`), and a
  docker job that builds the image, runs the container, and checks `/api/health` and `/`.
- README: setup, env var table, Docker and dev instructions, API table, and test commands.

## Tests (pytest, Gemini always mocked, temp DB per test)
Cover the following:
- Parser: valid and invalid files, size, page and encoding limits.
- Gemini client: retry versus no-retry behavior, error leakage, braces in user text.
- Auth: register/login, duplicate emails, password hashing, bad and expired tokens.
- Access control: every protected route returns 401 without a token; users can't see each
  other's analyses.
- Rate limits: each limit, `Retry-After`, window expiry, and the Gemini-failure refund.
- Static serving: the SPA fallback and path traversal.

## Done means
All tests pass, `npm run build` succeeds, `docker compose up --build` serves the app at
http://localhost:8000, and you can register, analyze a resume and see it in History. Be honest
about anything you couldn't verify, such as a live Gemini call without credits or visual checks
without a browser.
