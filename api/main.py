import importlib.util
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from api.core.config import settings
from api.core.database import init_db, SessionLocal
from api.models.tables import Project
from api.routers import ai, billing, hosted, insights, integrations, projects, public
from api.services import billing_service
from api.services.watch_service import watch_manager
from sqlalchemy import select


async def _upgrade_dev_projects_to_pro() -> None:
    if not settings.billing_mock_mode:
        return
    async with SessionLocal() as db:
        result = await db.execute(select(Project).where(Project.plan == "starter"))
        rows = result.scalars().all()
        for project in rows:
            project.plan = "pro"
        if rows:
            await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _upgrade_dev_projects_to_pro()
    watch_manager.start()
    yield
    if watch_manager._task:
        watch_manager._task.cancel()


app = FastAPI(
    title=settings.app_name,
    description="Auto-generate API docs, pytest scaffolds, and Django ER diagrams from your codebase.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)


_LANDING_PATH = Path(__file__).resolve().parent / "web" / "landing.html"


def _api_landing_html() -> str:
    template = _LANDING_PATH.read_text(encoding="utf-8")
    return template.replace("{{frontend_url}}", settings.frontend_url.rstrip("/"))


@app.get("/", include_in_schema=False)
async def root():
    return HTMLResponse(_api_landing_html())

_cors_origins = list(settings.cors_origins)
if settings.frontend_url and settings.frontend_url not in _cors_origins:
    _cors_origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"^https://[a-zA-Z0-9-]+\.onrender\.com$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(integrations.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(insights.router, prefix="/api/v1")
app.include_router(public.router, prefix="/api/v1")
app.include_router(hosted.router, prefix="/api/v1")


@app.get("/badge/{slug}.svg", include_in_schema=False)
async def short_badge(slug: str):
    """Shorter README URL (maps to hosted specwright.app/badge/{slug})."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(
        url=f"/api/v1/badge/{slug}.svg",
        status_code=302,
    )


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "product": settings.app_name}


@app.get("/api/v1/health/billing")
async def health_billing():
    from api.services.stripe_resilience import stripe_health_snapshot

    return {
        "status": "ok" if billing_service.billing_configured() else "missing_config",
        "billing": {
            "stripe_secret_key": bool(settings.stripe_secret_key.strip()),
            "stripe_webhook_secret": bool(settings.stripe_webhook_secret.strip()),
            "stripe_price_id_starter": bool(settings.stripe_price_id_starter.strip()),
            "stripe_price_id_pro": bool(settings.stripe_price_id_pro.strip()),
            "stripe_sdk_installed": importlib.util.find_spec("stripe") is not None,
        },
        "webhook_url_path": "/api/v1/billing/webhook",
        "required_webhook_events": ["checkout.session.completed"],
        "resilience": stripe_health_snapshot(),
    }


@app.get("/api/v1/product")
async def product():
    return {
        "name": "Specwright",
        "tagline": "The documentation layer for FastAPI teams — automatically.",
        "outputs": ["openapi", "api_docs", "django_diagram", "django_docs", "tests"],
        "stack": "FastAPI + AST analysis",
        "roadmap_shipped": [
            "github_pr_comments",
            "watch_mode",
            "llm_polish",
            "grounded_ai_suite",
            "stripe_billing",
            "public_score_badge",
            "team_dashboard",
        ],
        "roadmap_planned": [
            "app_specwright_io_saas_deploy",
        ],
    }
