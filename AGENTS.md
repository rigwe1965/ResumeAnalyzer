# AGENTS.md

Reference notes for AI agents (Claude Code and others) working in this repository.

## Project

**Resume Analyzer** — currently a fresh/empty repo (no application code yet). This file
exists to record the tooling and integrations already wired up so future sessions don't
have to rediscover them.

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

## Product roadmap (from Jira: KAN-5, KAN-6, KAN-7)

These three tickets define the intended tech stack and build order for this app. Treat
them as the source of truth for architecture until real code/ADRs supersede them.

### KAN-5 — Project scaffolding (FastAPI + React + Gemini smoke test)
- Backend: **FastAPI**, run locally via `uvicorn`.
- Frontend: **React (Vite)**, run locally via `npm run dev`.
- One test endpoint `/api/ping-gemini`: sends a hardcoded prompt to the **Gemini API**
  and returns the response.
- Frontend has one button that calls this endpoint and displays the result — proves
  frontend → backend → Gemini wiring before real feature work starts.
- No database work in this task.
- `.env.example` must include a `GEMINI_API_KEY` placeholder; the real key must never
  be committed (`.gitignore` the real `.env`).

### KAN-6 — Resume + JD upload → analysis report (core feature)
- User uploads a resume (`.pdf` or `.md`) and pastes/uploads a job description
  (plain text paste).
- Backend extracts text from the resume file, sends resume text + JD text to Gemini,
  and returns a structured report: a fitment score plus recommendations (missing
  keywords, skill gaps, phrasing suggestions).
- Frontend renders the report in a readable format after upload.
- Must handle errors gracefully (bad file type, empty JD, etc.).

### KAN-7 — Persist analysis results to SQLite
- Add **SQLite** storage: every analysis run (resume text, JD text, fitment score,
  recommendations, timestamp) is saved immediately after KAN-6's report is generated.
- Add a GET endpoint (+ basic frontend view) listing past analyses with score and
  timestamp — a simple history view so results survive a page refresh.
- DB file is created automatically on first run if it doesn't exist (no manual
  migration step expected at this stage).

## Notes for scaffolding future work

- No backend or frontend code exists yet as of this writing. Use standard, idiomatic
  layouts (`backend/` for FastAPI, `frontend/` for the Vite React app) unless the user
  specifies otherwise.
- Tech stack, per the roadmap above: **FastAPI + React/Vite + Gemini API + SQLite**
  (SQLite arrives in KAN-7, not before).
- Resume parsing must support both PDF and Markdown input (KAN-6).
- Never commit real API keys — use `.env.example` placeholders and `.gitignore` real `.env` files.
