import json
from pathlib import Path

from api.analyzers.django_models import analyze_django_models, collect_django_model_names
from api.analyzers.discovery import collect_python_files, detect_framework
from api.analyzers.route_collector import analyze_api_documentation, collect_all_routes
from api.analyzers.test_scaffold import generate_tests
from api.models.tables import Artifact, Scan
from api.services.artifact_sync import sync_artifacts_to_disk
from api.services.ai_breaking_change import classify_pr_diff
from api.services.ai_post_scan import run_post_scan_ai
from api.services.health_score import build_alerts, build_project_health


async def run_scan(
    project, db, *, trigger: str = "manual", previous_openapi: str | None = None
) -> Scan:
    root = Path(project.root_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Path not found: {root}")

    scan = Scan(
        project_id=project.id,
        status="running",
        summary="Analyzing codebase…",
        trigger=trigger,
    )
    db.add(scan)
    await db.flush()

    framework = project.framework if project.framework != "auto" else detect_framework(root)
    files = collect_python_files(root)

    routes: list[dict] = []
    artifacts_data: list[tuple[str, str, str, str]] = []

    # Django model diagrams + reference
    mermaid, models_md = analyze_django_models(files, root)
    artifacts_data.append(("django_diagram", "Django ER Diagram", mermaid, "diagrams/models.mmd"))
    artifacts_data.append(("django_docs", "Django Model Reference", models_md, "docs/models.md"))

    # API docs (FastAPI decorators or Django urls.py)
    openapi, api_md = analyze_api_documentation(files, root, framework)
    artifacts_data.append(("openapi", "OpenAPI Specification", openapi, "docs/openapi.yaml"))
    artifacts_data.append(("api_docs", "API Reference (Markdown)", api_md, "docs/api.md"))

    routes = collect_all_routes(files, root, framework)

    django_models = collect_django_model_names(files, root)
    test_code = generate_tests(
        framework=framework,
        routes=routes,
        models=django_models,
        project_name=project.name,
    )
    artifacts_data.append(("tests", "Pytest Scaffold", test_code, "tests/test_generated.py"))

    readme = _readme_bundle(project.name, framework, len(files), len(routes), len(django_models))
    artifacts_data.append(("readme", "Generation Summary", readme, "SPECWRIGHT_OUTPUT.md"))

    artifact_rows: list[Artifact] = []
    for kind, title, content, fpath in artifacts_data:
        art = Artifact(
            scan_id=scan.id,
            kind=kind,
            title=title,
            content=content,
            file_path=fpath,
        )
        db.add(art)
        artifact_rows.append(art)
    await db.flush()

    health = build_project_health(root, artifact_rows, previous_openapi)
    synced: list[str] = []
    if project.watch_enabled or trigger in (
        "watch",
        "manual",
        "connect",
        "github_connect",
    ):
        synced = sync_artifacts_to_disk(root, artifact_rows)

    stats = {
        "framework": framework,
        "files_scanned": len(files),
        "routes_found": len(routes),
        "models_found": len(django_models),
        "artifacts_generated": len(artifacts_data),
        "synced_files": synced,
        "score": health["score"],
        "coverage": health["coverage"],
        "drift": health["drift"],
        "pr_diff": health.get("pr_diff"),
        "metrics": health.get("metrics"),
        "alerts": health.get("alerts"),
        "models_count": health.get("models_count", 0),
        "breaking_change": classify_pr_diff(health.get("pr_diff")),
    }

    ai_patch = await run_post_scan_ai(
        project,
        routes,
        artifact_rows,
        stats,
        db,
        previous_openapi=previous_openapi,
    )
    stats.update(ai_patch)
    from api.services.post_scan_sync import run_post_scan_sync

    sync_patch = await run_post_scan_sync(project, artifact_rows, stats)
    stats.update(sync_patch)

    from api.services.autopilot import run_post_scan_autopilot

    autopilot_patch = await run_post_scan_autopilot(
        project, artifact_rows, routes, stats, root
    )
    stats.update(autopilot_patch)

    health = build_project_health(root, artifact_rows, previous_openapi)
    stats["score"] = health["score"]
    stats["coverage"] = health["coverage"]
    stats["metrics"] = health.get("metrics")
    stats["alerts"] = build_alerts(
        stats["coverage"],
        stats.get("pr_diff"),
        ai=stats.get("ai"),
        route_count=len(routes),
        framework=framework,
    )
    project.last_score = health["score"]["score"]

    scan.status = "completed"
    score_val = health["score"]["score"]
    ai = stats.get("ai") or {}
    extra = []
    if ai.get("descriptions_filled"):
        extra.append(f"AI filled {ai['descriptions_filled']} descriptions")
    if ai.get("tests_enhanced"):
        extra.append(f"AI enhanced {ai['tests_enhanced']} tests")
    if ai.get("migration_note"):
        extra.append("migration note ready")
    if stats.get("ci_synced"):
        extra.append("CI workflow synced")
    if stats.get("notion_page_url"):
        extra.append("Notion updated")
    ap = stats.get("autopilot") or {}
    if ap.get("all_pass"):
        extra.append("autopilot checks passed")
    elif ap.get("tests_gaps_after", 0) == 0 and ap.get("enabled"):
        extra.append("all routes scaffolded")
    scan.summary = (
        f"Scanned {len(files)} files · {len(routes)} routes · "
        f"Specwright Score {score_val}/100"
        + (f" · synced {len(synced)} files" if synced else "")
        + (f" · {' · '.join(extra)}" if extra else "")
    )
    scan.stats = json.dumps(stats)
    await db.flush()
    return scan


def _readme_bundle(name, framework, files, routes, models) -> str:
    return f"""# Specwright output — {name}

## What we generated
- **OpenAPI 3.1** from FastAPI route decorators
- **Markdown API reference** for your team / customers
- **Mermaid ER diagram** from Django models
- **Pytest scaffold** with smoke tests per route/model

## Scan stats
| Metric | Value |
|--------|-------|
| Framework | `{framework}` |
| Python files | {files} |
| API routes | {routes} |
| Django models | {models} |

## Next steps
1. Review `docs/openapi.yaml` in your CI docs pipeline
2. Copy `tests/test_generated.py` and add real fixtures
3. Paste `diagrams/models.mmd` into Notion or export PNG

_Auto-generated — developers hate writing docs; Specwright does the first 80%._
"""
