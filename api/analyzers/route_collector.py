"""Unified API route discovery (FastAPI + Django)."""
from __future__ import annotations

from pathlib import Path

from api.analyzers.django_url_scanner import collect_django_routes
from api.analyzers.discovery import detect_framework
from api.analyzers.fastapi_scanner import analyze_fastapi, collect_routes


def _django_backend_root(root: Path) -> Path:
    """Prefer apps/backend when Django API lives below monorepo root."""
    for candidate in (root / "apps" / "backend", root / "backend", root):
        if (candidate / "manage.py").exists():
            return candidate
    return root


def collect_all_routes(files: list[Path], root: Path, framework: str) -> list[dict]:
    routes = collect_routes(files, root)
    django_root = _django_backend_root(root)
    if framework == "django" or not routes:
        django_files = files
        if django_root != root:
            from api.analyzers.discovery import collect_python_files

            django_files = collect_python_files(django_root)
        django_routes = collect_django_routes(django_files, root)
        seen = {(r["method"], r["path"]) for r in routes}
        for r in django_routes:
            key = (r["method"], r["path"])
            if key not in seen:
                routes.append(r)
                seen.add(key)
    return routes


def analyze_api_documentation(files: list[Path], root: Path, framework: str) -> tuple[str, str]:
    from api.analyzers.fastapi_scanner import _markdown_api, _openapi_yaml

    routes = collect_all_routes(files, root, framework)
    if routes:
        return _openapi_yaml(routes), _markdown_api(routes)
    return analyze_fastapi(files, root)
