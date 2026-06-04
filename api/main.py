from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from api.core.config import settings
from api.core.database import init_db
from api.routers import ai, billing, insights, integrations, projects
from api.services.watch_service import watch_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(integrations.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(insights.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "product": settings.app_name}


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
        ],
    }
