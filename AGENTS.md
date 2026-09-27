# AGENTS.md

Reference notes for AI agents (Claude Code and others) working in this repository.

## Project

**Resume Analyzer** — a working FastAPI + React app. Upload a resume (`.pdf`/`.md`) and a
job description; Gemini returns a fitment score plus recommendations, which are persisted
to SQLite and browsable in a history view. This file exists to record the tooling,
integrations, and implemented architecture so future sessions don't have to rediscover them.

- Repo: https://github.com/Obinwanne1/Resume_Analyzer
- Default branch: `main`
- Owner/git identity: Romanus Ikechukwu Igwe (`iromanus@gmail.com`)

## Jira

- Connected via the Atlassian MCP server (`mcp__atlassian__*` tools).
- Site: `https://iromanus.atlassian.net` (cloudId `d354cb79-5741-473f-a9b0-4d2e53e3b668`).
- Project: **KAN** — "Resume Analyzer" (software, team-managed/simplified).
- Workflow statuses seen so far: `To Do` → `In Progress` / `Waiting for Customer` → `Resolved`
  (the "Resolved" status is the Done-category status; there is no status literally named "Done").
- Issue type used for early tasks: `Incident`.
- When asked to move a ticket to "done", transition it to `Resolved`, not a status named "Done".

## GitHub

- Connected via the GitHub MCP server (`mcp__github__*` tools).
- Remote: `Obinwanne1/Resume_Analyzer`.
- Standard PR workflow applies: check for a PR template before opening PRs, use
  `pull_request_review_write` (create → add comments → submit) for line-specific reviews.

## MCP servers available in this environment

- `atlassian` — Jira + Confluence (issues, transitions, comments, pages).
- `github` — repo, issues, PRs, branches, releases.
- `claude_ai` — Claude Docs, Gmail, Google Drive connectors.
- `ide` — diagnostics / code execution in the editor.

## Claude Code plugins installed

- `feature-dev` — feature-dev skill plus `code-architect`, `code-explorer`, and
  `code-reviewer` subagents for planning and reviewing feature work.
- `code-simplifier` — `code-simplifier` subagent for post-change cleanup/simplification.
- `frontend-design` — guidance skill for intentional, non-templated UI/visual design.

## Commit / PR attribution

Commits and PR descriptions created by Claude Code in this repo should end with:

```
Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
```

PR descriptions additionally end with:

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Implemented architecture

Tech stack: **FastAPI + React/Vite + Gemini API + SQLite**. Built out across Jira tickets
KAN-5 (scaffolding), KAN-6 (analysis feature), and KAN-7 (SQLite persistence) — all three
are done; treat the code below as the source of truth over the original ticket text.

### Backend (`backend/`)
- `app/main.py` — FastAPI app (`Resume Analyzer API`). CORS allows `http://localhost:5173`
  only. Reads `GEMINI_API_KEY` and `GEMINI_MODEL` (default `gemini-3.8-flash`) from `.env`.
  - `GET /api/ping-gemini` — smoke-test endpoint, sends a hardcoded prompt to Gemini.
  - `POST /api/analyze` — multipart form (`resume` file + `job_description` text). Extracts
    resume text, calls Gemini for a structured `AnalysisReport`, saves it, returns the
    saved `AnalysisRecord`.
  - `GET /api/analyses` — list of `AnalysisSummary` (id, filename, score, created_at),
    newest first.
  - `GET /api/analyses/{id}` — full `AnalysisRecord` for one saved analysis, 404 if missing.
- `app/resume_parser.py` — extracts text from `.pdf` (via `pypdf`) or `.md` uploads.
- `app/gemini_client.py` — calls Gemini and parses its response into an `AnalysisReport`.
- `app/schemas.py` — Pydantic models: `AnalysisReport` (score, missing_keywords,
  skill_gaps, phrasing_suggestions), `AnalysisRecord` (adds id/resume_filename/created_at),
  `AnalysisSummary` (list-view subset).
- `app/db.py` — SQLite (`backend/data/resume_analyzer.db`, auto-created on startup via
  `init_db()`). Single `analyses` table; JSON-encodes the list fields as TEXT columns.
- Run locally: `uvicorn app.main:app --reload` from `backend/` (needs `GEMINI_API_KEY` in
  `backend/.env`).

### Frontend (`frontend/`)
- React + Vite, plain CSS (no component library). Dev proxy sends `/api/*` to
  `http://localhost:8000` (`vite.config.js`).
- `src/App.jsx` — top-level layout + tab switcher between **Analyze** and **History**.
- `src/components/UploadForm.jsx` — resume file input + job description textarea, posts
  to `/api/analyze`.
- `src/components/ReportView.jsx` — renders an `AnalysisRecord`/report: score, missing
  keywords, skill gaps, phrasing suggestions.
- `src/components/HistoryList.jsx` — fetches `/api/analyses`, lists past runs, fetches
  and shows one full record (via `ReportView`) on selection.
- **Visual theme**: a "redlined document / editor's markup" look — serif body copy
  (`Source Serif 4`) with a handwritten accent font (`Kalam`) for red-ink annotations
  (score stamp, keyword underlines, margin carets). Theme tokens (`--paper`, `--ink`,
  `--red`, `--rule`, etc.) live in `src/index.css` as CSS custom properties, with a
  `prefers-color-scheme: dark` override block — keep new UI on these tokens rather than
  hardcoding colors so dark mode stays correct. Run `npm run dev` from `frontend/`.
- Known environment issue (not code-related): `npm run lint` (oxlint) fails on this
  machine — a Windows Application Control policy blocks its native binding
  (`oxlint.win32-x64-msvc.node`). Use `npm run build` to catch compile errors instead.

## Notes for future work

- Resume parsing supports `.pdf` and `.md` only — reject/handle other types explicitly.
- Never commit real API keys — use `.env.example` placeholders and `.gitignore` real `.env` files.
- No browser automation tool (chromium-cli, browser MCP) is available in this environment;
  verify frontend changes via `npm run build` + manual review, and say so explicitly rather
  than claiming a visual check that didn't happen.
