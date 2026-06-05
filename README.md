# Specwright

<p align="center">
  <strong>The documentation layer for FastAPI teams — automatically.</strong>
</p>

<p align="center">
  <a href="https://github.com/dallas8000-ops/Specwright">Repository</a>
  · <a href="https://specwright-web.onrender.com">Live demo</a>
  · <a href="https://specwright-web.onrender.com/try">Try GitHub</a>
  · Team dashboard · Specwright Score · Watch mode · Grounded AI
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-Vite-61DAFB?logo=react&logoColor=black" alt="React + Vite" />
  <img src="https://img.shields.io/badge/OpenAPI-3.1-6BA539?logo=openapiinitiative&logoColor=white" alt="OpenAPI 3.1" />
  <img src="https://img.shields.io/badge/Team-dashboard-live-22D3EE" alt="Team dashboard" />
  <img src="https://img.shields.io/badge/AI-grounded-Pro-8B5CF6" alt="Grounded AI (Pro)" />
</p>

> **Repo tagline (for GitHub About):** *AST-synced API docs, OpenAPI, tests, and Specwright Score across all your repos — with a team dashboard, weekly drift alerts, and PR migration notes.*

Specwright reads your codebase (**AST analysis**, not guesswork) and keeps **OpenAPI**, **markdown API reference**, **pytest scaffolds**, and **ER diagrams** aligned with your routes and models. Swagger, Redoc, and Postman assume you maintain the spec by hand. Specwright attaches to the repo and updates artifacts on scan or on save.

## What problem it solves

| Pain | How Specwright helps |
|------|----------------------|
| Docs drift after every PR | Watch mode re-scans and writes `docs/openapi.yaml`, tests, and markdown to disk |
| No visibility across repos | **Team dashboard** — all projects, scores, weekly drift, coverage trends |
| No one knows test/doc coverage | **Specwright Score** (0–100) + per-route health (docs, tests, sync) |
| Reviewers miss API changes | PR comments, OpenAPI diff, **client migration notes** (Pro + AI) |
| CI ships stale specs | `specwright.yml` template fails the build when committed OpenAPI lags code |
| Docs live in three places | One scan → OpenAPI, markdown, Notion export, GitHub comment |

## Core features

| Feature | What it does |
|---------|----------------|
| **Public score badge** | Shields-style SVG for GitHub READMEs — viral discovery (Codecov / Snyk pattern) |
| **Team dashboard** | All repos in one view: scores, 7-day deltas, drift-this-week, team & per-repo trends |
| **Specwright Score** | Weighted health: API docs, test coverage, spec freshness, model docs |
| **Route health dashboard** | Method badges, coverage labels, metric cards, action banners |
| **Watch + live sync** | Polls the tree (~3s); SSE updates; writes artifacts into the repo |
| **PR-aware diffing** | Compare OpenAPI to previous scan; enriched GitHub PR comments |
| **Drift + Slack** | Alerts when on-disk spec is behind code |
| **CI template** | `GET /projects/{id}/ci-template` → GitHub Action yaml |
| **Notion export** | Push latest API markdown to a Notion page |
| **Grounded AI suite** (Pro) | Description fill, migration notes, test bodies, scoped chat — see below |
| **AI polish** (Pro) | LLM improves markdown grammar/clarity — paths stay exact |

Deterministic scan/score/CI stays AST-based. LLM features are gated on `SPECWRIGHT_AI_API_KEY` + Pro plan.

## Team dashboard (multi-repo)

Built for tech leads and EMs overseeing **3–8 codebases**. Open **Team** in the app or `GET /api/v1/dashboard`.

| View | What you see |
|------|----------------|
| **Summary** | Project count, avg Specwright Score, avg doc/test coverage, drifted-this-week |
| **Drifted this week** | Repos with spec drift, stale scans (>7 days), or never scanned |
| **All projects** | Sortable table: score, 7d Δ, doc %, test %, sync status, last scan |
| **Team score trend** | Weekly average score from scan history (last 8 weeks) |
| **Per-repo history** | Sparklines from recent scans — no extra storage required |

Connect each repo on **Connect** (`/`), run **Generate artifacts**, then review the portfolio on `/dashboard`.

## Public score badge (README embed)

After a scan, open any project → **README score badge** → copy markdown into your repo:

```markdown
[![Specwright Score 84](http://localhost:8080/api/v1/badge/project-a1b2c3d4e5f6.svg)](http://localhost:8080/api/v1/p/project-a1b2c3d4e5f6)
```

| URL | Purpose |
|-----|---------|
| `GET /api/v1/badge/{slug}.svg` | Badge image (public, cacheable) |
| `GET /badge/{slug}.svg` | Short alias (302 → above) |
| `GET /api/v1/p/{slug}` | Landing page when visitors click the badge |
| `GET /api/v1/projects/{id}/badge-embed` | Markdown snippet + hosted URL hints |

Each project gets a stable `public_slug` (e.g. `project-a1b2c3d4e5f6`). When you deploy to production, point `SPECWRIGHT_PUBLIC_API_URL` at your API host so READMEs use:

`https://specwright.app/badge/{slug}.svg` (same path pattern as [Codecov](https://docs.codecov.com/docs) / [Snyk](https://snyk.io) badges).

## Grounded AI (Pro / Enterprise)

**AST owns truth; AI owns prose.** All features use routes from the last scan — unknown paths are rejected or flagged.

| Feature | Endpoint | What it does |
|---------|----------|----------------|
| **AI suite summary** | `GET .../ai/suite` | Gap counts, breaking-change triage (no LLM) |
| **Fill descriptions** | `POST .../ai/descriptions` | Weak OpenAPI summaries → docstring-backed text |
| **Migration note** | `POST .../ai/migration-note` | Client-facing PR paragraph from diff + score |
| **Breaking-change triage** | `GET .../ai/breaking-changes` | Removed = breaking, added = additive |
| **Docstring reconcile** | `GET .../ai/reconcile` | Handler doc vs generated summary mismatches |
| **Test bodies** | `POST .../ai/tests` | Grounded pytest bodies for scaffold functions |
| **Scoped chat** | `POST .../ai/chat` | “How do I…?” over OpenAPI + handler snippets |
| **AI polish** | `POST .../artifacts/{id}/polish` | Improve markdown artifacts |

GitHub PR comments automatically include **breaking-change triage**, **migration note** (when AI is configured), and **reconcile counts**.

**Auto on scan (Pro + `SPECWRIGHT_AI_API_KEY`):** weak OpenAPI descriptions are filled from docstrings; when the spec diff shows route changes, a **client migration note** is generated on the Score dashboard and in PR comments. Disable with `SPECWRIGHT_AI_AUTO_ON_SCAN=false`.

## Hosted preview (no local install)

Paste a public **GitHub URL** and get a Specwright Score without connecting a local path.

| Step | Action |
|------|--------|
| UI | Open **Try GitHub** (`/try`) or call the API |
| API | `POST /api/v1/hosted/preview` with `{ "github_url": "https://github.com/org/repo" }` |
| Server | Requires **git** on the API host (shallow clone, 120s timeout) |

This is the foundation for **`app.specwright.io`** — same scan engine, zero venv setup for evaluators. Connect the repo locally afterward for watch mode, badges, and team dashboard.

**Live on Render:**

- App: [https://specwright-web.onrender.com](https://specwright-web.onrender.com)
- Try GitHub: [https://specwright-web.onrender.com/try](https://specwright-web.onrender.com/try)
- API health: [https://specwright-api.onrender.com/api/v1/health](https://specwright-api.onrender.com/api/v1/health)
- Badge: `https://specwright-api.onrender.com/api/v1/badge/{slug}.svg`

## Framework support

| Framework | Status |
|-----------|--------|
| FastAPI | Live — route discovery, OpenAPI, tests |
| Django | Live — models, Mermaid ER, admin-oriented docs |
| Express.js | Roadmap |
| Ruby on Rails | Roadmap |
| Laravel | Roadmap |

## Architecture

```
Specwright-/
├── api/          # Specwright backend (FastAPI, port 8080)
├── frontend/     # React + Vite UI (port 5173+)
├── backend/      # Legacy Django app (not wired in current UI)
└── scripts/dev.ps1
```

- **Database:** SQLite async (`SPECWRIGHT_DATABASE_URL`, default `sqlite+aiosqlite:///specwright.db`)
- **Env prefix:** `SPECWRIGHT_` on all settings (avoids clashing with a global `DATABASE_URL`)

## App routes (UI)

| Path | Purpose |
|------|---------|
| `/dashboard` | **Team dashboard** — all projects, scores, weekly drift, trends |
| `/` | Connect codebase, recent projects, roadmap |
| `/project/:id` | Specwright Score, Grounded AI, integrations, artifacts |
| `/try` | **Hosted preview** — paste a public GitHub URL, get a score |
| `/billing` | Starter / Pro / Enterprise pricing |
| `/api` | In-app API hub (Swagger, ReDoc, health, product) |

Backend landing (same visual language): http://localhost:8080

## Deploy on Render

Blueprint file: `render.yaml` — two services:

| Service | URL (default name) | Runtime |
|---------|-------------------|---------|
| `specwright-api` | `https://specwright-api.onrender.com` | Docker (FastAPI + git for hosted preview) |
| `specwright-web` | `https://specwright-web.onrender.com` | Static (Vite React) |

**First deploy**

1. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint** → connect [dallas8000-ops/Specwright](https://github.com/dallas8000-ops/Specwright)
2. After services are created, set env vars:

| Service | Variable | Value |
|---------|----------|-------|
| `specwright-api` | `SPECWRIGHT_FRONTEND_URL` | `https://specwright-web.onrender.com` |
| `specwright-api` | `SPECWRIGHT_PUBLIC_API_URL` | `https://specwright-api.onrender.com` |
| `specwright-api` | `SPECWRIGHT_PUBLIC_SITE_URL` | `https://specwright-web.onrender.com` |
| `specwright-web` | `VITE_API_URL` | `https://specwright-api.onrender.com/api/v1` |

3. **Manual Deploy** on both services (or push to `main` if auto-deploy is on).

**Free tier notes:**

- Persistent disks are **not** supported on free web services — do not add a `disk:` block to `render.yaml`.
- SQLite URL must be `sqlite+aiosqlite:///specwright.db` (relative to `/app`). Paths like `///tmp/...` fail because SQLAlchemy treats them as relative and the parent dir may not exist.
- Data resets on redeploy — fine for demos; upgrade the API plan + disk, or use PostgreSQL, for durable storage.

**Redeploy** — push to `main` or click **Manual Deploy → Deploy latest commit** on each service. After changing `VITE_API_URL`, redeploy **specwright-web** (value is baked in at build time).

Health check: `GET https://specwright-api.onrender.com/api/v1/health`

## Quick start

```powershell
git clone https://github.com/dallas8000-ops/Specwright.git
cd Specwright
copy .env.specwright.example .env

# API venv (first time)
python -m venv api\.venv
api\.venv\Scripts\pip install -r api\requirements.txt

# UI (first time)
cd frontend; npm install; cd ..

# One-shot dev (two terminal windows)
.\scripts\dev.ps1

# Or manually:
api\.venv\Scripts\uvicorn api.main:app --reload --port 8080
cd frontend; npm run dev
```

1. Open http://localhost:5173  
2. **Connect** — add one or more codebases (absolute paths)  
3. **Generate artifacts** on each project  
4. Open **Team** (`/dashboard`) for portfolio scores and drift  
5. Optional: **Watch**, **GitHub**, **Slack**, **CI yaml**, **AI** (Pro)

Demo target: scan the `api/` folder in this repo twice to see score trends and PR diff.

## API reference

| Endpoint | Description |
|----------|-------------|
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

Full list: UI **API** tab or http://localhost:8080

## Pricing

| Tier | Price | Highlights |
|------|-------|------------|
| Starter | $29/mo | Scans, watch, exports, CI artifacts, team dashboard |
| Pro | $79/mo | + Grounded AI, auto description fill & migration notes, GitHub PR automation |
| Enterprise | Custom | SSO, SLA, dedicated support |

Configure display prices with `SPECWRIGHT_STARTER_PRICE_USD` / `SPECWRIGHT_PRO_PRICE_USD`.

## Configuration

Copy `.env.specwright.example` to `.env` in the repo root (or set variables in the shell).

```env
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

**GitHub webhook:** `POST /api/v1/github/webhook` on pull request events (set `github_repo` on the project as `owner/repo`).

## License

Proprietary / project-local — adjust as needed for your distribution.
