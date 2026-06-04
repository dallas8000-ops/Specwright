# Specwright

<p align="center">
  <strong>The documentation layer for FastAPI teams — automatically.</strong>
</p>

<p align="center">
  <a href="https://github.com/dallas8000-ops/Specwright-">Repository</a>
  · AST-grounded OpenAPI · Specwright Score · Watch mode · PR migration notes
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-Vite-61DAFB?logo=react&logoColor=black" alt="React + Vite" />
  <img src="https://img.shields.io/badge/OpenAPI-3.1-6BA539?logo=openapiinitiative&logoColor=white" alt="OpenAPI 3.1" />
  <img src="https://img.shields.io/badge/AI-grounded-Pro-8B5CF6" alt="Grounded AI (Pro)" />
</p>

> **Repo tagline (for GitHub About):** *AST-synced API docs, OpenAPI, tests, and Specwright Score for FastAPI teams — with PR-aware migration notes.*

Specwright reads your codebase (**AST analysis**, not guesswork) and keeps **OpenAPI**, **markdown API reference**, **pytest scaffolds**, and **ER diagrams** aligned with your routes and models. Swagger, Redoc, and Postman assume you maintain the spec by hand. Specwright attaches to the repo and updates artifacts on scan or on save.
## What problem it solves

| Pain | How Specwright helps |
|------|----------------------|
| Docs drift after every PR | Watch mode re-scans and writes `docs/openapi.yaml`, tests, and markdown to disk |
| No one knows test/doc coverage | **Specwright Score** (0–100) + per-route health (docs, tests, sync) |
| Reviewers miss API changes | PR comments and OpenAPI diff: new/removed paths, score, gaps |
| CI ships stale specs | `specwright.yml` template fails the build when committed OpenAPI lags code |
| Docs live in three places | One scan → OpenAPI, markdown, Notion export, GitHub comment |

## Core features

| Feature | What it does |
|---------|----------------|
| **Specwright Score** | Weighted health: API docs, test coverage, spec freshness, model docs |
| **Route health dashboard** | Method badges, coverage labels, metric cards, action banners |
| **Watch + live sync** | Polls the tree (~3s); SSE updates; writes artifacts into the repo |
| **PR-aware diffing** | Compare OpenAPI to previous scan; enriched GitHub PR comments |
| **Drift + Slack** | Alerts when on-disk spec is behind code |
| **CI template** | `GET /projects/{id}/ci-template` → GitHub Action yaml |
| **Notion export** | Push latest API markdown to a Notion page |
| **AI polish** (Pro) | LLM improves markdown grammar/clarity — paths stay exact |
| **Grounded AI suite** (Pro) | Descriptions, migration notes, test bodies, scoped chat — see below |

Deterministic scan/score/CI stays AST-based. LLM features are gated on `SPECWRIGHT_AI_API_KEY` + Pro plan.

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

**Auto on scan (Pro + `SPECWRIGHT_AI_API_KEY`):** weak OpenAPI descriptions are filled from docstrings; when the spec diff shows route changes, a **client migration note** is generated and shown on the Score dashboard (and in PR comments). Disable with `SPECWRIGHT_AI_AUTO_ON_SCAN=false`.

UI: project page → Score banners + **Grounded AI** panel for manual reruns.

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
AutomationFlow/
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
| `/` | Connect codebase, recent projects, roadmap |
| `/project/:id` | Specwright Score, integrations, artifact viewer |
| `/billing` | Starter / Pro / Enterprise pricing |
| `/api` | In-app API hub (Swagger, ReDoc, health, product) |

Backend landing (same visual language): http://localhost:8080

## Quick start

```powershell
git clone https://github.com/dallas8000-ops/Specwright-.git
cd Specwright-
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
2. **Analyze codebase** — use an absolute path (e.g. `...\AutomationFlow\api`)  
3. **Generate artifacts** on the project page  
4. Optional: enable **Watch**, connect **GitHub**, set **Slack**, export **CI yaml**

Demo target: scan the `api/` folder in this repo.

## API reference

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health` | Liveness |
| `GET /api/v1/product` | Product metadata |
| `GET /api/v1/roadmap` | Framework roadmap |
| `GET /api/v1/docs` | Swagger UI |
| `POST /api/v1/projects` | Register codebase path |
| `POST /api/v1/projects/{id}/scan` | Run analyzers |
| `GET /api/v1/projects/{id}/health` | Score + coverage + alerts |
| `GET /api/v1/projects/{id}/ai/suite` | AI insight summary |
| `POST /api/v1/projects/{id}/ai/chat` | Scoped how-to Q&A (Pro) |
| `GET /api/v1/projects/{id}/watch/events` | SSE watch stream |
| `POST /api/v1/github/webhook` | PR-triggered rescan + comment |

Full list: UI **API** tab or http://localhost:8080

## Pricing

| Tier | Price | Highlights |
|------|-------|------------|
| Starter | $29/mo | Scans, watch, exports, CI artifacts |
| Pro | $79/mo | + AI polish, GitHub PR automation |
| Enterprise | Custom | SSO, SLA, dedicated support |

Configure display prices with `SPECWRIGHT_STARTER_PRICE_USD` / `SPECWRIGHT_PRO_PRICE_USD`.

## Configuration

Copy `.env.specwright.example` to `.env` in the repo root (or set variables in the shell).

```env
SPECWRIGHT_FRONTEND_URL=http://localhost:5173

# Catalog (billing page)
SPECWRIGHT_STARTER_PRICE_USD=29
SPECWRIGHT_PRO_PRICE_USD=79

# GitHub PR comments + webhook
SPECWRIGHT_GITHUB_TOKEN=
SPECWRIGHT_GITHUB_WEBHOOK_SECRET=

# AI polish (Pro+) — OpenAI-compatible API
SPECWRIGHT_AI_API_KEY=
SPECWRIGHT_AI_API_BASE_URL=https://api.openai.com/v1
SPECWRIGHT_AI_MODEL=gpt-4o-mini

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
