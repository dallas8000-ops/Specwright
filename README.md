# Specwright

**The documentation layer for FastAPI and Django teams — automatically.**

[Live demo](https://specwright-web-production.up.railway.app) · [Try GitHub](https://specwright-web-production.up.railway.app/try) · [Repository](https://github.com/dallas8000-ops/Specwright)

`Python 3.11+` · `FastAPI` · `React + Vite` · `OpenAPI 3.1` · `Team dashboard` · `Grounded AI (Pro)`

> **Repo "About" tagline:** AST-synced API docs, OpenAPI, tests, and Specwright Score across all your repos — with a team dashboard, weekly drift alerts, and PR migration notes.

Specwright reads your codebase through AST analysis — not guesswork — and keeps OpenAPI, a markdown API reference, pytest scaffolds, and ER diagrams aligned with your actual routes and models. Swagger, Redoc, and Postman assume you maintain the spec by hand. Specwright attaches to the repo and rewrites those artifacts on every scan or on save, so the docs can't silently drift away from the code.

---

## Live demo

| | |
|---|---|
| **App** | https://specwright-web-production.up.railway.app |
| **Try GitHub** (paste a public repo, get a score) | https://specwright-web-production.up.railway.app/try |
| **API health** | `GET https://specwright-api-production.up.railway.app/api/v1/health` |

> Deployed on **Railway** as two services — a web frontend and an API backend.

---

## What problem it solves

| Pain | How Specwright helps |
|---|---|
| Docs drift after every PR | Watch mode re-scans and writes `docs/openapi.yaml`, tests, and markdown to disk |
| No visibility across repos | Team dashboard — all projects, scores, weekly drift, coverage trends |
| No one knows test/doc coverage | Specwright Score (0–100) + per-route health (docs, tests, sync) |
| Reviewers miss API changes | PR comments, OpenAPI diff, client migration notes (Pro + AI) |
| CI ships stale specs | `specwright.yml` template fails the build when committed OpenAPI lags code |
| Docs live in three places | One scan → OpenAPI, markdown, Notion export, GitHub comment |

---

## Core features

| Feature | What it does |
|---|---|
| Public score badge | Shields-style SVG for GitHub READMEs (the Codecov / Snyk discovery pattern) |
| Team dashboard | All repos in one view: scores, 7-day deltas, drift-this-week, per-repo trends |
| Specwright Score | Weighted health: API docs, test coverage, spec freshness, model docs |
| Route health dashboard | Method badges, coverage labels, metric cards, action banners |
| Watch + live sync | Polls the tree (~3s); SSE updates; writes artifacts into the repo |
| PR-aware diffing | Compare OpenAPI to previous scan; enriched GitHub PR comments |
| Drift + Slack alerts | Notifies when the on-disk spec falls behind the code |
| CI template | `GET /projects/{id}/ci-template` → GitHub Action YAML |
| Notion export | Push latest API markdown to a Notion page |
| Grounded AI suite (Pro) | Description fill, migration notes, test bodies, scoped chat |
| AI polish (Pro) | LLM improves markdown grammar/clarity — paths stay exact |

Deterministic scan / score / CI stays AST-based. LLM features are gated behind `SPECWRIGHT_AI_API_KEY` + a Pro plan.

---

## Team dashboard (multi-repo)

Built for tech leads and EMs overseeing 3–8 codebases. Open **Team** in the app or `GET /api/v1/dashboard`.

| View | What you see |
|---|---|
| Summary | Project count, avg Specwright Score, avg doc/test coverage, drifted-this-week |
| Drifted this week | Repos with spec drift, stale scans (>7 days), or never scanned |
| All projects | Sortable table: score, 7d Δ, doc %, test %, sync status, last scan |
| Team score trend | Weekly average score from scan history (last 8 weeks) |
| Per-repo history | Sparklines from recent scans — no extra storage required |

Connect each repo on **Connect** (`/`), run **Generate artifacts**, then review the portfolio on `/dashboard`.

---

## Public score badge (README embed)

After a scan, open any project → **README score badge** → copy the markdown into your repo. The badge path follows the same pattern as Codecov / Snyk:

```
[![Specwright Score 84](https://specwright-api-production.up.railway.app/api/v1/badge/{slug}.svg)](https://specwright-api-production.up.railway.app/api/v1/p/{slug})
```

| URL | Purpose |
|---|---|
| `GET /api/v1/badge/{slug}.svg` | Badge image (public, cacheable) |
| `GET /badge/{slug}.svg` | Short alias (302 → above) |
| `GET /api/v1/p/{slug}` | Landing page when visitors click the badge |
| `GET /api/v1/projects/{id}/badge-embed` | Markdown snippet + hosted URL hints |

Each project gets a stable `public_slug` (e.g. `project-a1b2c3d4e5f6`). In production, set `SPECWRIGHT_PUBLIC_API_URL` to your Railway API host so generated badge markdown points at the right place.

---

## Grounded AI (Pro / Enterprise)

AST owns truth; AI owns prose. Every feature uses routes from the last scan — unknown paths are rejected or flagged.

| Feature | Endpoint | What it does |
|---|---|---|
| AI suite summary | `GET .../ai/suite` | Gap counts, breaking-change triage (no LLM) |
| Fill descriptions | `POST .../ai/descriptions` | Weak OpenAPI summaries → docstring-backed text |
| Migration note | `POST .../ai/migration-note` | Client-facing PR paragraph from diff + score |
| Breaking-change triage | `GET .../ai/breaking-changes` | Removed = breaking, added = additive |
| Docstring reconcile | `GET .../ai/reconcile` | Handler doc vs generated summary mismatches |
| Test bodies | `POST .../ai/tests` | Grounded pytest bodies for scaffold functions |
| Scoped chat | `POST .../ai/chat` | "How do I…?" over OpenAPI + handler snippets |
| AI polish | `POST .../artifacts/{id}/polish` | Improve markdown artifacts |

GitHub PR comments automatically include breaking-change triage, a migration note (when AI is configured), and reconcile counts.

Auto-on-scan (Pro + `SPECWRIGHT_AI_API_KEY`): weak OpenAPI descriptions are filled from docstrings; when the spec diff shows route changes, a client migration note is generated on the Score dashboard and in PR comments. Disable with `SPECWRIGHT_AI_AUTO_ON_SCAN=false`.

---

## Hosted preview (no local install)

Paste a public GitHub URL and get a Specwright Score without connecting a local path.

| Step | Action |
|---|---|
| UI | Open **Try GitHub** (`/try`) or call the API |
| API | `POST /api/v1/hosted/preview` with `{ "github_url": "https://github.com/org/repo" }` |
| Server | Requires `git` on the API host (shallow clone, 120s timeout) |

Same scan engine as the local flow, zero venv setup for evaluators. Connect the repo locally afterward for watch mode, badges, and the team dashboard.

---

## Framework support

| Framework | Status |
|---|---|
| FastAPI | **Live** — route discovery, OpenAPI, tests |
| Django | **Live** — models, Mermaid ER, admin-oriented docs |
| Express.js | Roadmap |
| Ruby on Rails | Roadmap |
| Laravel | Roadmap |

---

## Architecture

```
Specwright/
├── api/          # Specwright backend (FastAPI, port 8080)
├── frontend/     # React + Vite UI (port 5173+)
├── backend/      # Legacy Django app (not wired into the current UI)
└── scripts/dev.ps1
```

- **Database:** SQLite async (`SPECWRIGHT_DATABASE_URL`, default `sqlite+aiosqlite:///specwright.db`)
- **Env prefix:** `SPECWRIGHT_` on all settings (avoids clashing with a global `DATABASE_URL`)

---

## App routes (UI)

| Path | Purpose |
|---|---|
| `/dashboard` | Team dashboard — all projects, scores, weekly drift, trends |
| `/` | Connect codebase, recent projects, roadmap |
| `/project/:id` | Specwright Score, Grounded AI, integrations, artifacts |
| `/try` | Hosted preview — paste a public GitHub URL, get a score |
| `/billing` | Starter / Pro / Enterprise pricing |
| `/api` | In-app API hub (Swagger, ReDoc, health, product) |

---

## Deploy (Railway)

Specwright runs as **two Railway services** — an API (Docker, FastAPI + `git` for hosted preview) and a static web frontend (Vite React). The repo includes a blueprint to provision both.

After the services are created, set these environment variables:

| Service | Variable | Value |
|---|---|---|
| API | `SPECWRIGHT_FRONTEND_URL` | your web service URL |
| API | `SPECWRIGHT_PUBLIC_API_URL` | your API service URL |
| API | `SPECWRIGHT_PUBLIC_SITE_URL` | your web service URL |
| web | `VITE_API_URL` | `<your API URL>/api/v1` |

After changing `VITE_API_URL`, redeploy the web service — the value is baked in at build time.

> **Note on storage:** the default SQLite URL must stay relative (`sqlite+aiosqlite:///specwright.db`). For durable storage across redeploys, attach a Railway PostgreSQL service and point `SPECWRIGHT_DATABASE_URL` at it.

**Health check:** `GET https://specwright-api-production.up.railway.app/api/v1/health`

---

## Quick start (local)

```bash
git clone https://github.com/dallas8000-ops/Specwright.git
cd Specwright
copy .env.specwright.example .env

# API venv (first time)
python -m venv api\.venv
api\.venv\Scripts\pip install -r api\requirements.txt

# UI (first time)
cd frontend && npm install && cd ..

# One-shot dev (two terminal windows)
.\scripts\dev.ps1

# Or manually:
api\.venv\Scripts\uvicorn api.main:app --reload --port 8080
cd frontend && npm run dev
# Open http://localhost:5173
```

Then: **Connect** one or more codebases (absolute paths) → **Generate artifacts** on each → open **Team** (`/dashboard`) for portfolio scores and drift. Optional: Watch, GitHub, Slack, CI YAML, AI (Pro).

---

## CI

GitHub Actions workflow: `.github/workflows/ci-smoke.yml`. Three independent checks on push/PR:

- Frontend unit smoke (`npm run test:run`)
- API tests with coverage gate (`--cov-fail-under=30`)
- Backend pytest with coverage gate (`--cov-fail-under=60`, configured in `backend/pytest.ini`)

These thresholds are conservative by design — they enforce a baseline in CI without blocking iteration.

---

## API reference

| Endpoint | Description |
|---|---|
| `GET /api/v1/health` | Liveness |
| `GET /api/v1/product` | Product metadata |
| `GET /api/v1/dashboard` | Multi-project scores, drift, team trends |
| `GET /api/v1/badge/{slug}.svg` | Public README score badge |
| `GET /api/v1/projects/{id}/badge-embed` | Copy-paste markdown for README |
| `POST /api/v1/hosted/preview` | GitHub URL → Specwright Score (hosted preview) |
| `GET /api/v1/roadmap` | Framework roadmap |
| `GET /api/v1/docs` | Swagger UI |
| `POST /api/v1/projects` | Register codebase path |
| `POST /api/v1/projects/{id}/scan` | Run analyzers |
| `GET /api/v1/projects/{id}/health` | Score + coverage + alerts |
| `GET /api/v1/projects/{id}/ai/suite` | AI insight summary |
| `POST /api/v1/projects/{id}/ai/descriptions` | Fill OpenAPI descriptions (Pro) |
| `POST /api/v1/projects/{id}/ai/migration-note` | PR migration note (Pro) |
| `POST /api/v1/projects/{id}/ai/chat` | Scoped how-to Q&A (Pro) |
| `GET /api/v1/projects/{id}/watch/events` | SSE watch stream |
| `POST /api/v1/github/webhook` | PR-triggered rescan + comment |

---

## Pricing

| Tier | Price | Highlights |
|---|---|---|
| Starter | $29/mo | Scans, watch, exports, CI artifacts, team dashboard |
| Pro | $79/mo | + Grounded AI, auto description fill & migration notes, GitHub PR automation |
| Enterprise | Custom | SSO, SLA, dedicated support |

Configure display prices with `SPECWRIGHT_STARTER_PRICE_USD` / `SPECWRIGHT_PRO_PRICE_USD`.

---

## Configuration

Copy `.env.specwright.example` to `.env` in the repo root (or set variables in the shell).

```bash
SPECWRIGHT_FRONTEND_URL=http://localhost:5173
SPECWRIGHT_PUBLIC_API_URL=http://localhost:8080
SPECWRIGHT_PUBLIC_SITE_URL=http://localhost:8080

# Catalog (billing page)
SPECWRIGHT_STARTER_PRICE_USD=29
SPECWRIGHT_PRO_PRICE_USD=79

# GitHub PR comments + webhook
SPECWRIGHT_GITHUB_TOKEN=
SPECWRIGHT_GITHUB_WEBHOOK_SECRET=

# AI (Pro+) — OpenAI-compatible API
SPECWRIGHT_AI_API_KEY=
SPECWRIGHT_AI_API_BASE_URL=https://api.openai.com/v1
SPECWRIGHT_AI_MODEL=gpt-4o-mini
SPECWRIGHT_AI_AUTO_ON_SCAN=true

# Integrations
SPECWRIGHT_SLACK_WEBHOOK_URL=
SPECWRIGHT_NOTION_API_KEY=
SPECWRIGHT_NOTION_PARENT_PAGE_ID=

# Stripe (production checkout)
SPECWRIGHT_STRIPE_SECRET_KEY=
SPECWRIGHT_STRIPE_WEBHOOK_SECRET=
SPECWRIGHT_STRIPE_PRICE_ID_STARTER=
SPECWRIGHT_STRIPE_PRICE_ID_PRO=

# Local only — mock checkout without Stripe
# SPECWRIGHT_BILLING_MOCK_MODE=true
```

GitHub webhook: `POST /api/v1/github/webhook` on pull-request events (set `github_repo` on the project as `owner/repo`).

---

## License

Proprietary / project-local — adjust as needed for your distribution.
